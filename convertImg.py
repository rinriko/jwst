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
    image_data = hdu.data
    hdu.header  # Header with 3 axes
    # Print the header to see details
    print("FITS Header:")
    print(hdu.header)


    # Define stretch functions with corresponding names
    stretches = [
        # (None, "No Stretch"),  # Case with no stretch
        # (SqrtStretch(), "Sqrt Stretch"),
        # (LogStretch(), "Log Stretch"),
        # (AsinhStretch(), "Asinh Stretch"),
        (LinearStretch(), "Linear Stretch")
    ]

    for stretch, stretch_name in stretches:
        # Adjust scale with the stretch function if provided, else only interval
        if stretch is not None:
            norm = ImageNormalize(image_data[s, :, :], interval=ZScaleInterval(), stretch=stretch)
        else:
            norm = ImageNormalize(image_data[s, :, :], interval=ZScaleInterval())

        # # Create axes with WCS projection
        # fig = plt.figure()
        # ax = fig.add_subplot(111, projection=wcs)
        # plt.imshow(image_data[s, :, :], origin='lower', cmap=plt.cm.gray, norm=norm)
        # ax.coords.grid(color='white', alpha=0.5, linestyle='solid')
        # plt.show()

        fig, ax = plt.subplots(figsize=(10, 8),subplot_kw={'projection': wcs, 'slices': ('x', 'y')})
        # ax = plt.subplot(projection=wcs, label='overlays')
        img = ax.imshow(image_data[s, :, :], cmap='viridis', norm=norm)

        ax.coords.grid(color='white', alpha=0.5, linestyle='solid')
        # Enable tick labels along grid lines
        # Set axis labels
        ra = ax.coords[0]
        dec = ax.coords[1]
        ra.set_axislabel('Right Ascension', fontsize=20, minpad=0.8)
        dec.set_axislabel('Declination', fontsize=20, minpad=-0.5)
        ra.set_major_formatter('hh:mm:ss.s')
        dec.set_major_formatter('dd:mm:ss.s')
        ra.set_ticks(number=100)
        dec.set_ticks(number=10)

        # ==================================================
    #    # Add annotation near the origin to indicate direction
    #     origin_x, origin_y = wcs.wcs_pix2world(0, 0, 0)  # Convert pixel (0, 0) to world coordinates

    #     # Convert the coordinates to the desired string format
    #     coord = SkyCoord(ra=origin_x * u.deg, dec=origin_y * u.deg, frame='icrs')
    #     formatted_x = coord.ra.to_string(unit=u.hour, precision=2)  # Format RA
    #     formatted_y = coord.dec.to_string(unit=u.deg, precision=2)   # Format Dec

    #     ax.annotate(f'({formatted_x}, {formatted_y})',
    #                 xy=(0, 0),
    #                 xytext=(-70, -20),
    #                 textcoords='offset points',
    #                 color='black',
    #                 fontsize=10,)


        # ==================================================
        # Add the title with the stretch name
        ax.set_title(f'{stretch_name}', fontsize=20)

        # Adding a color bar legend
        cbar = plt.colorbar(img, ax=ax, orientation="vertical", pad=0.1)
        cbar.set_label('Intensity', rotation=90, labelpad=10, fontsize=20)

        # Save the image with the legend, differentiated by stretch name
        plt.savefig(f'ImglongZsqrt_slice{s}_{stretch_name.replace(" ", "_").lower()}.png')
        # Show and clear each plot to avoid overlay
        # plt.show()
        # plt.close()


name = r'C:\Users\avmcc\Downloads\JWSTTiming-mains\JWSTTiming-main\MAST_2024-06-06T1429\MAST_2024-06-06T1429\JWST\jw01666001001_02102_00001-seg001_nrcb1\jw01666001001_02102_00001-seg001_nrcb1_o001_crfints.fits'
name = "T:\MAST_2023-10-07T0548\JWST\jw01666001001_02102_00001-seg001_nrcb1\jw01666001001_02102_00001-seg001_nrcb1_o001_crfints.fits"
name = "T:\MAST_2023-10-07T0548\JWST\jw01666001001_02102_00001-seg001_nrcblong\jw01666001001_02102_00001-seg001_nrcblong_o001_crfints.fits"
convertToPNG(50, name)