import matplotlib.pyplot as plt
from astropy.wcs import WCS
from astropy.io import fits
from astropy.utils.data import get_pkg_data_filename
from astropy import units as u
from astropy.visualization import ZScaleInterval, SqrtStretch, ImageNormalize
import matplotlib.pyplot as plt
from astropy.wcs import WCS, FITSFixedWarning
from astropy.io import fits
from astropy.visualization import ZScaleInterval, SqrtStretch, LogStretch, AsinhStretch, LinearStretch, ImageNormalize
import numpy as np
from astropy.coordinates import SkyCoord
import warnings

def convertToPNG(theSlice, filepath):
    s = theSlice
    filename = filepath 
    hdu = fits.open(filename)[1]  # Access the FITS data (typically second extension for image data)

    wcs = WCS(hdu.header, naxis=2)  # Create WCS object

    print(wcs)
    image_data = hdu.data
    hdu.header  # Header with 3 axes
    print("FITS Header:")
    print(hdu.header)


    stretches = [
        (LinearStretch(), "Linear Stretch")
    ]

    for stretch, stretch_name in stretches:
        # Adjust scale with the stretch function if provided, else only interval
        if stretch is not None:
            norm = ImageNormalize(image_data[s, :, :], interval=ZScaleInterval(), stretch=stretch)
        else:
            norm = ImageNormalize(image_data[s, :, :], interval=ZScaleInterval())


        fig, ax = plt.subplots(figsize=(10, 8),subplot_kw={'projection': wcs, 'slices': ('x', 'y')})
        img = ax.imshow(image_data[s, :, :], cmap='viridis', norm=norm,origin='lower')

        ra = ax.coords['ra']
        dec = ax.coords['dec']
        # ra = ax.coords['ra']
        ra.grid(color='lightgray', alpha=1, linestyle='solid')
        dec.grid(color='black', alpha=1, linestyle='solid')
        ra.set_ticklabel(color='dimgray', size=12)
        dec.set_ticklabel(color='black', size=12)

        ra.set_axislabel('Right Ascension', color='dimgray', fontsize=20, minpad=0.5)
        dec.set_axislabel('Declination', color='black', fontsize=20, minpad=0.5)
        ra.set_major_formatter('hh:mm:ss.s')
        dec.set_major_formatter('dd:mm:ss')
        ra.set_ticks(number=15)
        dec.set_ticks(number=10)

        ax.set_title(f'{stretch_name}', fontsize=20)

        plt.savefig(f'ImglongZsqrt_slice{s}_{stretch_name.replace(" ", "_").lower()}.png')


name = r'C:\Users\avmcc\Downloads\JWSTTiming-mains\JWSTTiming-main\MAST_2024-06-06T1429\MAST_2024-06-06T1429\JWST\jw01666001001_02102_00001-seg001_nrcb1\jw01666001001_02102_00001-seg001_nrcb1_o001_crfints.fits'
name = "T:\MAST_2023-10-07T0548\JWST\jw01666001001_02102_00001-seg001_nrcb1\jw01666001001_02102_00001-seg001_nrcb1_o001_crfints.fits"
name = "T:\MAST_2023-10-07T0548\JWST\jw01666001001_02102_00001-seg001_nrcblong\jw01666001001_02102_00001-seg001_nrcblong_o001_crfints.fits"
convertToPNG(50, name)