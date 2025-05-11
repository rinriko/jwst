from astropy.io import fits
from astropy.wcs import WCS
from astropy.visualization import ZScaleInterval, ImageNormalize, SqrtStretch
import numpy as np
import matplotlib.pyplot as plt

def convertToPNG(theSlice, filepath, output_png="out.png", fig_size=8, delta_deg=0.05):
    """
    Read slice `theSlice` from the second HDU of `filepath`,
    plot with a WCS grid + N/E arrows, and save to `output_png`.
    """
    # --- 1) Read the data + header
    with fits.open(filepath) as hdulist:
        hdu = hdulist[1]
        data = hdu.data
        header = hdu.header

    # pick theSlice if it’s a cube
    if data.ndim == 3:
        img = data[theSlice]
    else:
        img = data

    # --- 2) Build WCS + normalization
    wcs = WCS(header, naxis=2)
    norm = ImageNormalize(img, interval=ZScaleInterval(), stretch=SqrtStretch())

    # --- 3) Compute world‐coordinate extent of the image
    ny, nx = img.shape
    # pixel corners in (x, y)
    pix = np.array([[0,0], [nx,0], [0,ny], [nx,ny]])
    world = wcs.all_pix2world(pix, 0)  # shape (4,2): [ [ra,dec], ... ]
    ra_vals, dec_vals = world[:,0], world[:,1]
    extent = [ra_vals.min(), ra_vals.max(), dec_vals.min(), dec_vals.max()]

    # --- 4) Plot
    fig = plt.figure(figsize=(fig_size, fig_size))
    ax = fig.add_subplot(111, projection=wcs)
    ax.imshow(
        img,
        origin='lower',
        cmap='gray',
        norm=norm,
        extent=extent,
        transform=ax.get_transform('world')
    )

    # grid
    ax.coords.grid(True, color='cyan', linestyle='solid', linewidth=0.5)
    ax.coords[0].set_axislabel("RA")
    ax.coords[1].set_axislabel("Dec")

    # --- 5) Draw N/E arrows at center
    cx, cy = nx/2, ny/2
    ra0, dec0 = wcs.all_pix2world(cx, cy, 0)

    # north tip
    xN, yN = wcs.all_world2pix(ra0, dec0 + delta_deg, 0)
    # east tip (adjust for cos(dec))
    xE, yE = wcs.all_world2pix(
        ra0 + delta_deg/np.cos(np.deg2rad(dec0)),
        dec0,
        0
    )

    arrow_kw = dict(arrowstyle="->", color="red", linewidth=1)
    ax.annotate("", xy=(xN, yN), xytext=(cx, cy), arrowprops=arrow_kw)
    ax.text(xN, yN, "N", color="red", ha="center", va="bottom", fontsize=12)

    ax.annotate("", xy=(xE, yE), xytext=(cx, cy), arrowprops=arrow_kw)
    ax.text(xE, yE, "E", color="red", ha="left", va="center", fontsize=12)

    # --- 6) Tweak margins & save (no bbox_inches="tight")
    plt.subplots_adjust(left=0.05, right=0.95, bottom=0.05, top=0.95)
    plt.savefig(output_png, dpi=150)
    plt.close(fig)


name = "T:\MAST_2023-10-07T0548\JWST\jw01666001001_02102_00001-seg001_nrcblong\jw01666001001_02102_00001-seg001_nrcblong_o001_crfints.fits"
convertToPNG(50, name)
