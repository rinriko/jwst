# jwst_export.py
# Export JWST slice -> raw Float32 .bin + .meta.json (with WCS CD matrix + CRVAL/CRPIX)
from pathlib import Path
import json
import numpy as np
from astropy.io import fits
from astropy.wcs import WCS
from astropy.wcs.utils import proj_plane_pixel_scales
from astropy.visualization import ZScaleInterval
from reproject import reproject_interp


def _arcsec_per_pix(header):
    try:
        w = WCS(header, naxis=2).celestial
        deg_per_pix = proj_plane_pixel_scales(w)  # (dy, dx) in deg/pix
        return float(np.mean(deg_per_pix) * 3600.0)
    except Exception:
        return None


def _extract_wcs_bits(header):
    """Return CRVAL, CRPIX, CD (2x2), rotation (deg) from a header."""
    try:
        w = WCS(header, naxis=2).celestial
        cd = w.pixel_scale_matrix
        crval = list(map(float, w.wcs.crval))
        crpix = list(map(float, w.wcs.crpix))
        cd11, cd12, cd21, cd22 = cd[0, 0], cd[0, 1], cd[1, 0], cd[1, 1]
        theta_deg = float(np.degrees(np.arctan2(-cd12, cd22)))
        cd_out = [[float(cd11), float(cd12)], [float(cd21), float(cd22)]]
        return crval, crpix, cd_out, theta_deg
    except Exception:
        return None, None, None, None


def _load_slice(filepath: str, hdu_index: int, the_slice: int):
    with fits.open(filepath, memmap=True) as hdul:
        hdu = hdul[hdu_index]
        data = np.asarray(hdu.data)
        if data.ndim == 3:
            arr = np.asarray(data[the_slice, :, :], dtype=np.float32)
        elif data.ndim == 2:
            arr = np.asarray(data, dtype=np.float32)
        else:
            raise ValueError(f"Unsupported data ndim={data.ndim}")
        return arr, hdu.header


def _autocenter(arr: np.ndarray, mode="centroid", frac=0.001):
    h, w = arr.shape
    flat = arr.ravel()
    if mode == "max":
        idx = int(np.nanargmax(flat))
        y = idx // w
        x = idx - y * w
        return (float(x) + 0.5, float(y) + 0.5)

    finite_vals = flat[np.isfinite(flat)]
    if finite_vals.size == 0:
        return None
    n = flat.size
    k = max(1, int(round(n * frac)))
    kth = max(0, finite_vals.size - k)
    thresh = np.partition(finite_vals, kth)[kth]
    ys, xs = np.indices((h, w))
    mask = (arr >= thresh) & np.isfinite(arr)
    if not np.any(mask):
        return None
    wts = arr[mask].astype(np.float64)
    xs_sel = xs[mask].astype(np.float64) + 0.5
    ys_sel = ys[mask].astype(np.float64) + 0.5
    sw = wts.sum()
    if sw <= 0 or not np.isfinite(sw):
        return None
    cx = float((wts * xs_sel).sum() / sw)
    cy = float((wts * ys_sel).sum() / sw)
    return (cx, cy)


def exportRaw(
    theSlice: int,
    filepath: str,
    *,
    hdu: int = 1,
    out_prefix: str | None = None,
    autocenter: str = "centroid",
    reproject_northup: bool = True,
):
    """
    Export JWST slice -> .bin + .meta.json

    Strategy (matches your "correct image" PNG path):
      - Build a NEW header with diagonal CD (east-left, north-up)
      - Enlarge to a square 'diag x diag' canvas and re-center CRPIX to its middle
      - Reproject into that WCS using reproject_interp(shape_out=(diag, diag), order=0)
      - DO NOT flip array; the React overlay already handles Y inversion.
    """
    arr, header_in = _load_slice(filepath, hdu, theSlice)
    orig_wcs = WCS(header_in, naxis=2).celestial

    if reproject_northup:
        print("Reprojecting to north-up on a square canvas with diagonal CD...")

        ny, nx = arr.shape
        diag = int(np.hypot(ny, nx))  # big enough square to contain rotation

        # Compute pixel scale (deg/pix)
        pixscale = proj_plane_pixel_scales(orig_wcs)  # (deg/pix in Dec, deg/pix in RA) but we keep signs explicitly below

        # Build a new header by copying the original, then overwriting WCS keys
        new_hdr = header_in.copy()

        # Square output size
        new_hdr["NAXIS1"] = diag
        new_hdr["NAXIS2"] = diag

        # Center the reference pixel in the middle of the square
        new_hdr["CRPIX1"] = diag / 2 + 0.5
        new_hdr["CRPIX2"] = diag / 2 + 0.5

        # Keep CRVAL from the original (same sky center)
        # (copying header already kept CRVAL; no change needed)

        # Force diagonal CD: east-left, north-up
        new_hdr["CD1_1"], new_hdr["CD1_2"] = -pixscale[0], 0.0
        new_hdr["CD2_1"], new_hdr["CD2_2"] = 0.0, pixscale[1]

        # Build WCS and reproject
        new_wcs = WCS(new_hdr, naxis=2).celestial

        arr, _ = reproject_interp(
            (arr, orig_wcs),
            new_wcs,
            shape_out=(diag, diag),
            order=0,  # match your "correct image" code (nearest-neighbor)
        )
        arr = np.flipud(arr)
        header_out = new_wcs.to_header()
    else:
        header_out = header_in

    # ZScale for display normalization
    zmin, zmax = ZScaleInterval().get_limits(arr)

    # WCS attributes from the OUTPUT header (what the viewer needs)
    asp = _arcsec_per_pix(header_out)
    crval, crpix, cd, rotation_deg = _extract_wcs_bits(header_out)

    # Output paths
    if out_prefix is None:
        out_prefix = str("./") + f"slice{theSlice}"
    bin_path = Path(out_prefix).with_suffix(".bin")
    meta_path = Path(out_prefix).with_suffix(".meta.json")

    # Write raw float32 (little-endian), row-major
    arr.astype("<f4").tofile(bin_path)

    # (optional) center for overlay
    center_px = None if autocenter == "none" else _autocenter(arr, mode=autocenter)

    # Meta JSON for React overlay
    meta = {
        "width": int(arr.shape[1]),
        "height": int(arr.shape[0]),
        "dtype": "float32_le",
        "order": "row-major",
        "norm": {
            "kind": "linear",
            "source": "zscale",
            "vmin": float(zmin),
            "vmax": float(zmax),
        },
        "arcsec_per_pix": float(asp) if asp else None,
        "center_px": [float(center_px[0]), float(center_px[1])] if center_px else None,
        "crval": crval,    # [RAdeg, DECdeg]
        "crpix": crpix,    # [CRPIX1, CRPIX2] in the square canvas
        "cd": cd,          # 2x2 matrix (deg/pix), diagonal by construction
        "rotation_deg": rotation_deg,  # ~0 (by construction)
    }

    meta_path.write_text(json.dumps(meta, indent=2))
    print(f"Wrote {bin_path}")
    print(f"Wrote {meta_path}")
    if reproject_northup:
        print("→ North-up reprojected onto square canvas with diagonal CD (no overflow).")


# Example usage
if __name__ == "__main__":
    name = r"T:\JWST-Timing\MAST_2023-10-07T0548\JWST\jw01666001001_02102_00001-seg001_nrcblong\jw01666001001_02102_00001-seg001_nrcblong_o001_crfints.fits"
    exportRaw(50, name)
