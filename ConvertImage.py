import numpy as np
import matplotlib.pyplot as plt
import glob
from pathlib import Path
from astropy.io import fits
from astropy.wcs import WCS
from PIL import Image
from astropy.utils.data import get_pkg_data_filename
from astropy import units as u
from astropy.visualization import (ZScaleInterval, SqrtStretch, ImageNormalize)
from astropy.coordinates import SkyCoord
from astropy.wcs.utils import skycoord_to_pixel
import astropy.units as u
from astropy.wcs.utils import proj_plane_pixel_scales
import matplotlib.pyplot as plt
from astropy.visualization import ZScaleInterval, ImageNormalize, LinearStretch
from reproject import reproject_interp, reproject_exact

# Set the original path for FITS files
original_path = Path(r"T:/MAST_2023-10-07T0548/JWST")

# Set the output directories for full-size images and thumbnails
full_size_dir = Path(r"T:/jwst/static/img/full-size")
full_size_dir.mkdir(parents=True, exist_ok=True)
thumbnail_dir = Path(r"T:/jwst/static/img/thumbnails")
thumbnail_dir.mkdir(parents=True, exist_ok=True)

def old_convertToPNG(theSlice, filepath, output_dir):
    
    s = theSlice
    filename = filepath 
    
    hdu = fits.open(filename)[1] #Why are there two headers
    # wcs = WCS(hdu.header) # create wcs object
    wcs = WCS(hdu.header, naxis=2) # create wcs object
    image_data = hdu.data
    hdu.header # 3 axis

    #adjust scale
    norm = ImageNormalize(image_data[s, :, :], interval=ZScaleInterval())

    #axes object
    # ax = plt.subplot(projection=wcs, slices=('x', 'y', s)) # RA on X axis, Dec on Y axis for the slice s
    ax = plt.subplot(projection=wcs, slices=('x', 'y')) # RA on X axis, Dec on Y axis for the slice s
    ax.imshow(image_data[s, :, :], cmap='viridis', norm=norm) #order of axis is reversed???

    ra = ax.coords[0]
    dec = ax.coords[1]

    ra.set_axislabel('Right Ascension')
    dec.set_axislabel('Declination')
    
    # =====================================================================
    # plt.savefig('zsqrt_slice%s_seg001_nrcb1.png' % s)
    # Save the plot as PNG
    output_filename = Path(filename).stem + f'_slice{int(s)+1}.png'
    output_path = output_dir / output_filename
    plt.savefig(output_path)
    plt.close()  # Close the figure to release memory
    return output_path


def convertToPNG(theSlice, filepath, output_dir):
    s = theSlice
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
    
    # =====================================================================
    # plt.savefig('zsqrt_slice%s_seg001_nrcb1.png' % s)
    # Save the plot as PNG
    output_filename = Path(filename).stem + f'_slice{int(s)+1}.png'
    output_path = output_dir / output_filename
    plt.savefig(output_path)
    plt.close()  # Close the figure to release memory
    return output_path

# Function to create a thumbnail from a PNG image
def create_thumbnail(image_path, thumbnail_dir, size=(128, 128)):
    img = Image.open(image_path)
    img.thumbnail(size)
    thumbnail_path = thumbnail_dir / image_path.name
    img.save(thumbnail_path, "PNG")

for epoch in ["epoch1","epoch2"]:
    # for wave_type in ["sw"]:
    for wave_type in ["lw", "sw"]:
        if epoch == "epoch1":
            sw_files = sorted(original_path.glob("jw01666001001*_nrcb1/*crfints.fits"))
            lw_files = sorted(original_path.glob("jw01666001001*_nrcblong/*crfints.fits"))
        else:
            sw_files = sorted(original_path.glob("jw01666003001*_nrcb1/*crfints.fits"))
            lw_files = sorted(original_path.glob("jw01666003001*_nrcblong/*crfints.fits"))

        fileList = lw_files
        if wave_type == "sw":
            fileList = sw_files
        for filename in fileList:
            print(f"Processing {filename}...")
            f = fits.open(filename)
            data = f["SCI"]
            
            istart = 0  # there is no source in first few frames, this *could* cause a problem. Include them for now.
            iend = data.data.shape[0]            
            # for i in range(0,1):
            for i in range(istart, iend+1):
                print("File: ",filename ," Frame: ", i+1)
                full_size_output_dir = full_size_dir/ epoch/ wave_type
                full_size_output_dir.mkdir(parents=True, exist_ok=True)
                thumbnail_output_dir = thumbnail_dir/ epoch/ wave_type
                thumbnail_output_dir.mkdir(parents=True, exist_ok=True)
                try:
                    output_path = convertToPNG(i, filename, full_size_output_dir)
                    # Create a thumbnail of the saved PNG
                    create_thumbnail(output_path, thumbnail_output_dir)
                except Exception as e:
                    print("Error: ", filename)
                    print(e)
                    print("----------------------------------------------------------------------------------------------------------------------")
            
            f.close()
            print(f"Finished {filename}...")
            print("===========================================================================================================================")

print("Conversion completed.")
