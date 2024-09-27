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

# Set the original path for FITS files
original_path = Path(r"T:/MAST_2023-10-07T0548/JWST")

# Set the output directories for full-size images and thumbnails
full_size_dir = Path(r"T:/jwst/static/img/full-size")
full_size_dir.mkdir(parents=True, exist_ok=True)
thumbnail_dir = Path(r"T:/jwst/static/img/thumbnails")
thumbnail_dir.mkdir(parents=True, exist_ok=True)

def convertToPNG(theSlice, filepath, output_dir):
    
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
