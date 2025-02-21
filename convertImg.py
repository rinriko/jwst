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

    wcs.wcs.ctype = ['RA---TAN', 'DEC--TAN']
    #represents a 0-degree rotation
    wcs.wcs.cd = [[1, 0],
                    [0, 1]]
    
    print(wcs)
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
        ax.coords.grid(True)
        # ax.coords.grid(color='white', alpha=1, linestyle='solid')
        # Enable tick labels along grid lines
        # Set axis labels

        # In Galactic coordinates, so the coordinates are called glon and glat. 
        # For an image in equatorial coordinates, you would use ra and dec. 
        # The names are only available for specific celestial coordinate systems - for all other systems, 
        # you should use the index of the coordinate (0 or 1).

        ra = ax.coords['ra']
        dec = ax.coords['dec']
        # ra = ax.coords['ra']
        ra.grid(color='lightgray', alpha=1, linestyle='solid')
        dec.grid(color='black', alpha=1, linestyle='solid')
        ra.set_ticklabel(color='dimgray', size=12)
        dec.set_ticklabel(color='black', size=12)
        # ra.grid(color='blue', alpha=1, linestyle='solid')
        # dec.grid(color='darkred', alpha=1, linestyle='solid')
        # ra.set_ticklabel(color='royalblue', size=12)
        # dec.set_ticklabel(color='firebrick', size=12)

        ra.set_axislabel('Right Ascension', color='dimgray', fontsize=20, minpad=0.8)
        dec.set_axislabel('Declination', color='black', fontsize=20, minpad=-0.5)
        # ra = ax.coords['ra']
        ra.set_major_formatter('hh:mm:ss.s')
        dec.set_major_formatter('dd:mm:ss.s')
        ra.set_ticks(number=10)
        dec.set_ticks(number=10)
        # ra.set_ticks([242.2, 242.3, 242.4] * u.degree)

        # dec.set_ticks([242.2, 242.3, 242.4] * u.degree)
        # ra.set_ticks(spacing=10 * u.arcmin, color='yellow')
        # dec.set_ticks(spacing=10 * u.arcmin, color='orange')
        ra.set_ticklabel(exclude_overlapping=True)
        dec.set_ticklabel(exclude_overlapping=True)
        ra.set_ticklabel(simplify=False)
        dec.set_ticklabel(simplify=False)
        # ra.display_minor_ticks(True)
        # dec.display_minor_ticks(True)
        # dec.set_minor_frequency(10)
        # ra.set_ticklabel(simplify=False)
        # dec.set_ticklabel(simplify=False)
        # ra.set_ticks_position('#')
        # ra.set_ticklabel_position('#')
        # ra.set_axislabel_position('#')
        # dec.set_ticks_position('#')
        # dec.set_ticklabel_position('#')
        # dec.set_axislabel_position('#')

        # ra.add_tickable_gridline('i', -10*u.arcmin)

        # dec.set_ticks_position('li')
        # dec.set_ticklabel_position('li')
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