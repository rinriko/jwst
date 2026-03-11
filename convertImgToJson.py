import warnings
from astropy.wcs import FITSFixedWarning
warnings.filterwarnings('ignore', category=FITSFixedWarning)

import json
import numpy as np
from astropy.io import fits
from astropy.wcs import WCS
from astropy.wcs.utils import proj_plane_pixel_scales
from astropy.coordinates import SkyCoord
from astropy.visualization import ZScaleInterval, ImageNormalize, LinearStretch
from reproject import reproject_interp


def convertImgToJSON(
    theSlice,
    filepath,
    center_pix_orig=None,
    center_sky: SkyCoord=None,
    r_in=None,
    r_out=None,
    n_grid=10,
    save_json_path="output.json"
):
    """
    Export JWST FITS slice into a JSON file containing:
    - Rotated/north-up image
    - ZScale normalization
    - Full WCS metadata
    - RA/Dec grid lines (pixel coords)
    - RA/Dec tick labels (pixel coords)
    - Center pixel (optional)
    - Annulus radii (optional)
    """

    # ========== 1. Load slice ==========
    with fits.open(filepath) as hdul:
        hdu = hdul[1]
        data = hdu.data[theSlice]
        orig_wcs = WCS(hdu.header, naxis=2).celestial

    ny, nx = data.shape
    diag = int(np.hypot(ny, nx))

    # ========== 2. Build north-up WCS ==========
    hdr = hdu.header.copy()
    hdr["NAXIS1"] = diag
    hdr["NAXIS2"] = diag
    hdr["CRPIX1"] = diag / 2 + 0.5
    hdr["CRPIX2"] = diag / 2 + 0.5

    pixscale = proj_plane_pixel_scales(orig_wcs)
    hdr["CD1_1"], hdr["CD1_2"] = -pixscale[0], 0.0
    hdr["CD2_1"], hdr["CD2_2"] = 0.0, pixscale[1]

    new_wcs = WCS(hdr, naxis=2).celestial

    # ========== 3. Reproject =============
    array, footprint = reproject_interp(
        (data, orig_wcs),
        new_wcs,
        shape_out=(diag, diag),
        order=0
    )

    # ========== 4. ZScale normalization ==========
    interval = ZScaleInterval()
    vmin, vmax = interval.get_limits(array)
    # norm = ImageNormalize(array, interval=ZScaleInterval(), stretch=LinearStretch())

    # ========== 5. Center pixel transform ==========
    xy_disp = None
    if center_pix_orig is not None:
        x0, y0 = float(center_pix_orig[0]), float(center_pix_orig[1])
        sky = orig_wcs.pixel_to_world(x0, y0)
        px, py = new_wcs.world_to_pixel(sky)
        xy_disp = (float(px), float(py))
    elif center_sky is not None:
        px, py = new_wcs.world_to_pixel(center_sky)
        xy_disp = (float(px), float(py))

    # =====================================================
    # 6. Compute RA/Dec grid lines
    # =====================================================

    # determine RA/Dec bounds of the 4 corners
    H, W = diag, diag
    corners = np.array([
        [0, 0],
        [W - 1, 0],
        [0, H - 1],
        [W - 1, H - 1]
    ])
    sky = new_wcs.pixel_to_world(corners[:, 0], corners[:, 1])
    ra_vals = sky.ra.deg
    dec_vals = sky.dec.deg

    ra_min, ra_max = ra_vals.min(), ra_vals.max()
    dec_min, dec_max = dec_vals.min(), dec_vals.max()

    # evenly spaced grid
    ra_grid = np.linspace(ra_min, ra_max, n_grid)
    dec_grid = np.linspace(dec_min, dec_max, n_grid)

    # Sample functions
    def sample_constant_ra(ra_deg):
        # sample along dec direction
        decs = np.linspace(dec_min, dec_max, 300)
        world = SkyCoord(ra=ra_deg, dec=decs, unit="deg")
        px, py = new_wcs.world_to_pixel(world)
        pts = np.stack([px, py], axis=1)
        return pts.tolist()

    def sample_constant_dec(dec_deg):
        ras = np.linspace(ra_min, ra_max, 300)
        world = SkyCoord(ra=ras, dec=dec_deg, unit="deg")
        px, py = new_wcs.world_to_pixel(world)
        pts = np.stack([px, py], axis=1)
        return pts.tolist()

    # Grid lines
    ra_lines = [
        {
            "ra_deg": float(r),
            "pixels": sample_constant_ra(r)
        }
        for r in ra_grid
    ]

    dec_lines = [
        {
            "dec_deg": float(d),
            "pixels": sample_constant_dec(d)
        }
        for d in dec_grid
    ]

    # Tick labels
    def tick_ra(r):
        # pixel at bottom edge
        world = SkyCoord(ra=r, dec=dec_min, unit="deg")
        px, py = new_wcs.world_to_pixel(world)
        label = SkyCoord(ra=r, dec=0, unit="deg").ra.to_string(unit="hour", sep=":", precision=1)
        return {
            "px": [float(px), float(py)],
            "label": label
        }

    def tick_dec(d):
        world = SkyCoord(ra=ra_min, dec=d, unit="deg")
        px, py = new_wcs.world_to_pixel(world)
        label = SkyCoord(ra=0, dec=d, unit="deg").dec.to_string(unit="deg", sep=":", precision=1)
        return {
            "px": [float(px), float(py)],
            "label": label
        }

    ticks = {
        "ra": [tick_ra(r) for r in ra_grid],
        "dec": [tick_dec(d) for d in dec_grid]
    }
    # Convert to list and replace NaN/inf with None
    def sanitize(x):
        if isinstance(x, float) and (np.isnan(x) or np.isinf(x)):
            return None
        return x

    data_list = array.astype(np.float32).tolist()
    data_list = [[sanitize(v) for v in row] for row in data_list]
    # =====================================================
    # 7. Build JSON object
    # =====================================================
    result = {
        "meta": {
            "width": int(diag),
            "height": int(diag),
            "dtype": "float32_le",
            "order": "row-major",
            "norm": {
                "kind": "linear",
                "vmin": float(vmin),
                "vmax": float(vmax)
            },
            "crval": new_wcs.wcs.crval.tolist(),
            "crpix": new_wcs.wcs.crpix.tolist(),
            "cd": new_wcs.wcs.cd.tolist()
        },

        "data": data_list,

        "center": xy_disp,
        "r_in": r_in,
        "r_out": r_out,

        "grid": {
            "ra_lines": ra_lines,
            "dec_lines": dec_lines,
            "ticks": ticks
        }
    }

    # Save JSON
    with open(save_json_path, "w") as f:
        json.dump(result, f)

    return result


# -----------------------
# Example usage
# -----------------------
if __name__ == "__main__":
    from astropy.coordinates import SkyCoord
    import astropy.units as u

    fits_path =  r"T:\JWST-Timing\MAST_2023-10-07T0548\JWST\jw01666001001_02102_00001-seg001_nrcblong\jw01666001001_02102_00001-seg001_nrcblong_o001_crfints.fits"
    
    convertImgToJSON(
        theSlice=50,
        filepath=fits_path,
        center_pix_orig=(86.21004965, 75.37133730858254),
        r_in=[10],
        r_out=[30],
        save_json_path="slice50.json"
    )

    print("JSON exported → slice50.json")
