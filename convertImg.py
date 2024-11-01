import matplotlib.pyplot as plt
from astropy.wcs import WCS
from astropy.io import fits
from astropy.utils.data import get_pkg_data_filename
from astropy import units as u
from astropy.visualization import ZScaleInterval, SqrtStretch, ImageNormalize
import matplotlib.pyplot as plt
from astropy.wcs import WCS
from astropy.io import fits
from astropy.visualization import ZScaleInterval, SqrtStretch, LogStretch, AsinhStretch, LinearStretch, ImageNormalize


def convertToPNG(theSlice, filepath):
    
    s = theSlice
    filename = filepath 
    hdu = fits.open(filename)[1]  # Access the FITS data (typically second extension for image data)
    wcs = WCS(hdu.header, naxis=2)  # Create WCS object
    image_data = hdu.data
    hdu.header  # Header with 3 axes

    # Define stretch functions with corresponding names
    stretches = [
        (None, "No Stretch"),  # Case with no stretch
        (SqrtStretch(), "Sqrt Stretch"),
        (LogStretch(), "Log Stretch"),
        (AsinhStretch(), "Asinh Stretch"),
        (LinearStretch(), "Linear Stretch")
    ]

    for stretch, stretch_name in stretches:
        # Adjust scale with the stretch function if provided, else only interval
        if stretch is not None:
            norm = ImageNormalize(image_data[s, :, :], interval=ZScaleInterval(), stretch=stretch)
        else:
            norm = ImageNormalize(image_data[s, :, :], interval=ZScaleInterval())

        # Create axes with WCS projection
        fig, ax = plt.subplots(figsize=(10, 8),subplot_kw={'projection': wcs, 'slices': ('x', 'y')})
        img = ax.imshow(image_data[s, :, :], cmap='viridis', norm=norm)

        # Set axis labels
        ra = ax.coords[0]
        dec = ax.coords[1]
        ra.set_axislabel('Right Ascension', fontsize=20)
        dec.set_axislabel('Declination', fontsize=20)

        # Add the title with the stretch name
        ax.set_title(f'{stretch_name}', fontsize=20)

        # Adding a color bar legend
        cbar = plt.colorbar(img, ax=ax, orientation="vertical", pad=0.1)
        cbar.set_label('Intensity', rotation=90, labelpad=15, fontsize=20)

        # Save the image with the legend, differentiated by stretch name
        plt.savefig(f'ImglongZsqrt_slice{s}_{stretch_name.replace(" ", "_").lower()}.png')

        # Show and clear each plot to avoid overlay
        # plt.show()
        # plt.close()


name = r'C:\Users\avmcc\Downloads\JWSTTiming-mains\JWSTTiming-main\MAST_2024-06-06T1429\MAST_2024-06-06T1429\JWST\jw01666001001_02102_00001-seg001_nrcb1\jw01666001001_02102_00001-seg001_nrcb1_o001_crfints.fits'
name = "T:\MAST_2023-10-07T0548\JWST\jw01666001001_02102_00001-seg001_nrcb1\jw01666001001_02102_00001-seg001_nrcb1_o001_crfints.fits"
name = "T:\MAST_2023-10-07T0548\JWST\jw01666001001_02102_00001-seg001_nrcblong\jw01666001001_02102_00001-seg001_nrcblong_o001_crfints.fits"
convertToPNG(50, name)