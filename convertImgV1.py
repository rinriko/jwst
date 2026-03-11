import warnings
from astropy.wcs import FITSFixedWarning

# suppress that FITSFixedWarning
warnings.filterwarnings('ignore', category=FITSFixedWarning)

import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import rotate

from astropy.io import fits
from astropy.wcs import WCS
from astropy.visualization import (
    ZScaleInterval,
    ImageNormalize,
    LinearStretch,    # ← use a non-linear stretch!
)
from astropy.coordinates import SkyCoord
from astropy.wcs.utils import skycoord_to_pixel
import astropy.units as u
from astropy.wcs.utils import proj_plane_pixel_scales
import matplotlib.pyplot as plt
from astropy.visualization import ZScaleInterval, ImageNormalize, LinearStretch
from reproject import reproject_interp, reproject_exact

def convertToPNG(theSlice, filepath):
    number_size = 12
    label_size = 20
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

    plt.show()
    fig.savefig(
        'slice50_small.png',
        dpi=80,               # 80 dots/inch instead of 150
        bbox_inches='tight',  # trims the white border
        pad_inches=0.1
    )




name = r'C:\Users\avmcc\Downloads\JWSTTiming-mains\JWSTTiming-main\MAST_2024-06-06T1429\MAST_2024-06-06T1429\JWST\jw01666001001_02102_00001-seg001_nrcb1\jw01666001001_02102_00001-seg001_nrcb1_o001_crfints.fits'
name = "T:\MAST_2023-10-07T0548\JWST\jw01666001001_02102_00001-seg001_nrcb1\jw01666001001_02102_00001-seg001_nrcb1_o001_crfints.fits"
name = "T:\MAST_2023-10-07T0548\JWST\jw01666001001_02102_00001-seg001_nrcblong\jw01666001001_02102_00001-seg001_nrcblong_o001_crfints.fits"
convertToPNG(50, name)