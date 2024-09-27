import matplotlib.pyplot as plt
from astropy.wcs import WCS
from astropy.io import fits
from astropy.utils.data import get_pkg_data_filename

import matplotlib.pyplot as plt
from astropy import units as u

from astropy.visualization import (ZScaleInterval, SqrtStretch, ImageNormalize)

def convertToPNG(theSlice, filepath):
    
    s = theSlice
    filename = filepath 
    
    hdu = fits.open(filename)[1] #Why are there two headers
    wcs = WCS(hdu.header) # create wcs object
    image_data = hdu.data
    hdu.header # 3 axis

    #adjust scale
    norm = ImageNormalize(image_data[s, :, :], interval=ZScaleInterval())

    #axes object
    ax = plt.subplot(projection=wcs, slices=('x', 'y', s)) # RA on X axis, Dec on Y axis for the slice s
    ax.imshow(image_data[s, :, :], cmap='viridis', norm=norm) #order of axis is reversed???

    ra = ax.coords[0]
    dec = ax.coords[1]

    ra.set_axislabel('Right Ascension')
    dec.set_axislabel('Declination')

    plt.savefig('zsqrt_slice%s_seg001_nrcb1.png' % s)

name = r'C:\Users\avmcc\Downloads\JWSTTiming-mains\JWSTTiming-main\MAST_2024-06-06T1429\MAST_2024-06-06T1429\JWST\jw01666001001_02102_00001-seg001_nrcb1\jw01666001001_02102_00001-seg001_nrcb1_o001_crfints.fits'
name = "T:\MAST_2023-10-07T0548\JWST\jw01666001001_02102_00001-seg001_nrcb1\jw01666001001_02102_00001-seg001_nrcb1_o001_crfints.fits"
name = "T:\MAST_2023-10-07T0548\JWST\jw01666001001_02102_00001-seg001_nrcblong\jw01666001001_02102_00001-seg001_nrcblong_o001_crfints.fits"
convertToPNG(50, name)