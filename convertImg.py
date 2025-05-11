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
from matplotlib.patches import FancyArrowPatch
from astropy.coordinates import SkyCoord
from astropy.wcs.utils import skycoord_to_pixel
from matplotlib.patches import FancyArrowPatch

from matplotlib.patches import FancyArrowPatch
from astropy.coordinates import SkyCoord
from astropy.wcs.utils import skycoord_to_pixel

def draw_true_compass(ax, wcs, image_slice, delta_deg=0.2, color='red', label_color='white'):
    from matplotlib.patches import FancyArrowPatch
    from astropy.coordinates import SkyCoord
    from astropy.wcs.utils import skycoord_to_pixel

    ny, nx = image_slice.shape
    center_x, center_y = nx // 2, ny // 2
    center_coord = wcs.pixel_to_world(center_x, center_y)

    # Offset in world (RA/Dec) coordinates
    delta = delta_deg * u.deg
    directions = {
        'N': SkyCoord(ra=center_coord.ra, dec=center_coord.dec + delta),
        'E': SkyCoord(ra=center_coord.ra + delta, dec=center_coord.dec),
        'S': SkyCoord(ra=center_coord.ra, dec=center_coord.dec - delta),
        'W': SkyCoord(ra=center_coord.ra - delta, dec=center_coord.dec),
    }

    for label, coord in directions.items():
        try:
            end_x, end_y = skycoord_to_pixel(coord, wcs)
            arrow = FancyArrowPatch((center_x, center_y), (end_x, end_y),
                                    color=color, arrowstyle='->', linewidth=2, mutation_scale=15)
            ax.add_patch(arrow)
            ax.text(end_x, end_y, label,
                    color=label_color, fontsize=12,
                    ha='center', va='center',
                    bbox=dict(facecolor=color, edgecolor='none', boxstyle='circle,pad=0.3'))
        except Exception as e:
            print(f"Error drawing {label}: {e}")

def draw_image_axes(ax, length_px=50, color='cyan', label_color='cyan'):
    center_x, center_y = 100, 100  # small offset from corner

    ax.annotate('', xy=(center_x + length_px, center_y), xytext=(center_x, center_y),
                arrowprops=dict(arrowstyle='->', color=color, lw=2))
    ax.text(center_x + length_px + 10, center_y, 'X',
            color=label_color, fontsize=10, ha='left', va='center')

    ax.annotate('', xy=(center_x, center_y + length_px), xytext=(center_x, center_y),
                arrowprops=dict(arrowstyle='->', color=color, lw=2))
    ax.text(center_x, center_y + length_px + 10, 'Y',
            color=label_color, fontsize=10, ha='center', va='bottom')


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
        ra.set_ticklabel(color='gray', size=12)
        dec.set_ticklabel(color='black', size=12)

        ra.set_axislabel('Right Ascension', color='gray', fontsize=20, minpad=0.5)
        dec.set_axislabel('Declination', color='black', fontsize=20, minpad=0.5)
        ra.set_major_formatter('hh:mm:ss.s')
        dec.set_major_formatter('dd:mm:ss')
        ra.set_ticks(number=15)
        dec.set_ticks(number=10)

        ax.set_title(f'{stretch_name}', fontsize=20)

        plt.savefig(f'ImglongZsqrt_slice{s}_{stretch_name.replace(" ", "_").lower()}.png')

        # … immediately after saving your main figure …

        # create legend canvas
        fig2, ax2 = plt.subplots(figsize=(3,3))
        ax2.set_xlim(0,200);  ax2.set_ylim(0,200)
        ax2.axis('off')

        cx, cy = 100, 100   # center of legend
        L = 50             # arrow length in px

        # draw world‐compass arrows
        for dx, dy, lbl in [(0, L, 'N'),
                            (L, 0, 'E'),
                            (0, -L,'S'),
                            (-L,0, 'W')]:
            arr = FancyArrowPatch((cx,cy),
                                (cx+dx, cy+dy),
                                color='yellow',
                                arrowstyle='->',
                                linewidth=2,
                                mutation_scale=15)
            ax2.add_patch(arr)
            ax2.text(cx+dx, cy+dy, lbl,
                    color='yellow',
                    fontsize=12,
                    ha='center', va='center',
                    bbox=dict(facecolor='yellow',
                            edgecolor='none',
                            boxstyle='circle,pad=0.3'))

        # draw image‐axes in cyan
        draw_image_axes(ax2, length_px=L, color='cyan', label_color='cyan')

        # save legend
        fig2.savefig('orientation_legend.png',
                    dpi=150,
                    bbox_inches='tight',
                    pad_inches=0.1)
        plt.close(fig2)


name = r'C:\Users\avmcc\Downloads\JWSTTiming-mains\JWSTTiming-main\MAST_2024-06-06T1429\MAST_2024-06-06T1429\JWST\jw01666001001_02102_00001-seg001_nrcb1\jw01666001001_02102_00001-seg001_nrcb1_o001_crfints.fits'
name = "T:\MAST_2023-10-07T0548\JWST\jw01666001001_02102_00001-seg001_nrcb1\jw01666001001_02102_00001-seg001_nrcb1_o001_crfints.fits"
name = "T:\MAST_2023-10-07T0548\JWST\jw01666001001_02102_00001-seg001_nrcblong\jw01666001001_02102_00001-seg001_nrcblong_o001_crfints.fits"
convertToPNG(50, name)