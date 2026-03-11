import warnings
from astropy.wcs import FITSFixedWarning
warnings.filterwarnings('ignore', category=FITSFixedWarning)

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from astropy.io import fits
from astropy.wcs import WCS
from astropy.visualization import ZScaleInterval, ImageNormalize, LinearStretch
from astropy.wcs.utils import proj_plane_pixel_scales
from astropy.coordinates import SkyCoord
from reproject import reproject_interp

def convertToPNG(
    theSlice,
    filepath,
    center_pix_orig=None,
    center_sky: SkyCoord=None,  # OR a SkyCoord (RA/Dec)
    # --- Annulus radii (in displayed pixels) ---
    r_in: float=None,
    r_out: float=None,
    show_fill=False,
    save_path='slice.png'
):

    number_size = 12
    label_size  = 20

    with fits.open(filepath) as hdul:
        hdu      = hdul[1]
        data     = hdu.data[theSlice]                 # slice 50
        orig_wcs = WCS(hdu.header, naxis=2).celestial

    # 2) Build a new header where the CD matrix is purely diagonal:
    new_hdr = hdu.header.copy()

    # =============================================================
    # original XY shape
    ny, nx = data.shape

    # compute a big enough square to hold the rotated image
    diag = int(np.hypot(ny, nx))
    new_hdr['NAXIS1'] = diag
    new_hdr['NAXIS2'] = diag
    # recenter CRPIX so your image sits in the middle of that big square:
    new_hdr['CRPIX1'] = diag/2 + 0.5
    new_hdr['CRPIX2'] = diag/2 + 0.5

    # =============================================================
    # zero‐rotation CD as before
    # compute the pixel scale in degrees/pix
    pixscale = proj_plane_pixel_scales(orig_wcs)
    # zero out any rotation
    new_hdr['CD1_1'], new_hdr['CD1_2'] = -pixscale[0], 0.0
    new_hdr['CD2_1'], new_hdr['CD2_2'] =   0.0,        pixscale[1]
    new_wcs = WCS(new_hdr, naxis=2).celestial


    # 3) Reproject your slice onto that “north‐up, east‐right” WCS
    # array, footprint = reproject_exact(
    #     (data, orig_wcs),
    #     new_wcs,
    #     shape_out=data.shape
    # )
    array, footprint = reproject_interp(
        (data, orig_wcs),
        new_wcs,
        shape_out=(diag, diag),
        order=0                # 0 = nearest‐neighbor, 1 = linear (default)
    )

    # 4) Now plot with WCSAxes—axes will be straight
    norm = ImageNormalize(array, interval=ZScaleInterval(), stretch=LinearStretch())

    fig = plt.figure(figsize=(10,8))
    ax  = fig.add_subplot(1,1,1, projection=new_wcs)

    im = ax.imshow(array, origin='lower', cmap='viridis', norm=norm)

    # grid + ticks on straight RA/Dec
    ra = ax.coords['ra']
    dec = ax.coords['dec']
    ra.grid(color='lightgray', linestyle='solid')
    dec.grid(color='black',    linestyle='solid')
    ra.set_axislabel('Right Ascension', color='black', fontsize=label_size, minpad=0.8)
    dec.set_axislabel('Declination', color='black', fontsize=label_size, minpad=0.5)
    ra.set_ticks(number=10)
    dec.set_ticks(number=10)
    ra.set_ticklabel(size=number_size)
    dec.set_ticklabel(size=number_size)
    ra.set_major_formatter('hh:mm:ss.s')
    dec.set_major_formatter('dd:mm:ss')

    # plt.colorbar(im, ax=ax, label='Flux')
    cbar = plt.colorbar(im,
                    ax=ax,
                    label='Flux',
                    shrink=0.9,
                    aspect=25,
                    pad=0.04)
    cbar.ax.tick_params(labelsize=number_size)
    cbar.ax.yaxis.label.set_size(label_size)
    # plt.title('Slice 50 (linear stretch)')


    xy_disp = None

    if center_pix_orig is not None:
        # Convert original pixels -> sky -> displayed pixels
        x0, y0 = float(center_pix_orig[0]), float(center_pix_orig[1])
        sky = orig_wcs.pixel_to_world(x0, y0)
        x1, y1 = new_wcs.world_to_pixel(sky)
        xy_disp = (float(x1), float(y1))

    elif center_sky is not None:
        x1, y1 = new_wcs.world_to_pixel(center_sky)
        xy_disp = (float(x1), float(y1))



    # -----------------------
    # 6) Draw overlays (if any)
    # -----------------------
    if xy_disp is not None:
        x, y = xy_disp

        # Star marker at displayed pixels
        # ax.plot(x, y, marker='+', markersize=12, mew=2, color='white',
        #         transform=ax.get_transform('pixel'), zorder=5)

        # Draw annulus rings (displayed pixels)
        if r_out is not None:
            outer = Circle((x, y), r_out, fill=False, linewidth=1.8,
                           edgecolor='white', alpha=0.95,
                           transform=ax.get_transform('pixel'), zorder=5)
            ax.add_patch(outer)

        if r_in is not None:
            inner = Circle((x, y), r_in, fill=False, linewidth=1.2,
                           edgecolor='white', alpha=0.95, linestyle='--',
                           transform=ax.get_transform('pixel'), zorder=5)
            ax.add_patch(inner)

        # (Optional) Keep edges-only for photometry clarity; filled annulus often hides data.

    fig.savefig(save_path, dpi=150, bbox_inches='tight', pad_inches=0.1)
    # plt.close(fig)
    plt.show()
    return xy_disp  # so you can verify where the star landed


# -----------------------
# Example usage
# -----------------------
if __name__ == "__main__":
    from astropy.coordinates import SkyCoord
    import astropy.units as u

    name = r"T:\MAST_2023-10-07T0548\JWST\jw01666001001_02102_00001-seg001_nrcblong\jw01666001001_02102_00001-seg001_nrcblong_o001_crfints.fits"

    # CASE A: you only know the ORIGINAL (pre-rotation) pixel center:
    xy_disp = convertToPNG(
        theSlice=50,
        filepath=name,
        center_pix_orig=(86.21004965, 75.37133730858254),  # <- ORIGINAL pixels
        r_in=10,
        r_out=30,
        save_path='slice50_from_origpix_ring10_30.png'
    )
    print("Displayed pixels (from original):", xy_disp)

    # CASE B: you know the displayed pixels already (e.g., from a prior run):
    xy_disp2 = convertToPNG(
        theSlice=50,
        filepath=name,
        center_pix_orig=(86.21004965, 75.37133730858254), 
        r_in=10,
        r_out=40,
        save_path='slice50_from_disppix_ring10_40.png'
    )
    print("Displayed pixels (direct):", xy_disp2)

    # CASE C: if you know the sky coord:
    # sky = SkyCoord("15:39:00.00 +00:00:00.0", unit=(u.hourangle, u.deg))
    # convertToPNG(50, name, center_sky=sky, r_in=10, r_out=20, save_path='slice50_from_sky.png')
