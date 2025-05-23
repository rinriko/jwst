import matplotlib.pyplot as plt
from astropy.io import fits
from astropy.visualization import ZScaleInterval, ImageNormalize

def convertToPNG_simple(slice_index: int, fits_path: str, out_png: str):
    # Load the FITS data
    with fits.open(fits_path) as hdul:
        data = hdul[1].data          # assumes your image lives in extension 1

    # Extract the requested slice
    img_slice = data[slice_index, :, :]

    # Auto-scale with zscale
    norm = ImageNormalize(img_slice, interval=ZScaleInterval())

    # Plot only the image, no axes
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.imshow(img_slice, cmap='gray', norm=norm, origin='lower')
    ax.axis('off')   # <-- turns off x/y ticks and labels

    # Save
    fig.tight_layout(pad=0)
    fig.savefig(out_png, dpi=300, bbox_inches='tight', pad_inches=0)
    plt.close(fig)

# Example usage:
if __name__ == "__main__":
    fits_file = r"T:\MAST_2023-10-07T0548\JWST\jw01666001001_02102_00001-seg001_nrcblong\jw01666001001_02102_00001-seg001_nrcblong_o001_crfints.fits"
    convertToPNG_simple(
        slice_index=50,
        fits_path=fits_file,
        out_png="slice50_gray.png"
    )
