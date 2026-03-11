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
from pymongo import MongoClient
import config
from typing import Sequence, Tuple, Optional, List, Union
import matplotlib.patheffects as pe

import warnings
from astropy.wcs import FITSFixedWarning
warnings.filterwarnings('ignore', category=FITSFixedWarning)

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from astropy.io import fits
from astropy.wcs import WCS
from astropy.visualization import ZScaleInterval, ImageNormalize, LinearStretch
from astropy.wcs.utils import proj_plane_pixel_scales
from astropy.coordinates import SkyCoord
from reproject import reproject_interp

from concurrent.futures import ProcessPoolExecutor, as_completed
from astropy.io import fits
from pathlib import Path
import os, traceback

import os, traceback, multiprocessing as mp
# Set the original path for FITS files
original_path = Path(r"T:/MAST_2023-10-07T0548/JWST")

# Set the output directories for full-size images and thumbnails
full_size_dir = Path(r"T:/jwst/static/img/full-size")
full_size_dir.mkdir(parents=True, exist_ok=True)
full_size_with_annulus_dir = Path(r"T:/jwst/static/img/full-size-with-annulus")
full_size_with_annulus_dir.mkdir(parents=True, exist_ok=True)

zoom_dir = Path(r"T:/jwst/static/img/zoom")
zoom_dir.mkdir(parents=True, exist_ok=True)
thumbnail_dir = Path(r"T:/jwst/static/img/thumbnails")
thumbnail_dir.mkdir(parents=True, exist_ok=True)

OnlyImg_dir = Path(r"T:/jwst/static/img/OnlyImg")
OnlyImg_dir.mkdir(parents=True, exist_ok=True)
thumbnail_OnlyImg_dir = Path(r"T:/jwst/static/img/thumbnail_OnlyImg")
thumbnail_OnlyImg_dir.mkdir(parents=True, exist_ok=True)


# def old_convertToPNG(theSlice, filepath, output_dir):
    
#     s = theSlice
#     filename = filepath 
    
#     hdu = fits.open(filename)[1] #Why are there two headers
#     # wcs = WCS(hdu.header) # create wcs object
#     wcs = WCS(hdu.header, naxis=2) # create wcs object
#     image_data = hdu.data
#     hdu.header # 3 axis

#     #adjust scale
#     norm = ImageNormalize(image_data[s, :, :], interval=ZScaleInterval())

#     #axes object
#     # ax = plt.subplot(projection=wcs, slices=('x', 'y', s)) # RA on X axis, Dec on Y axis for the slice s
#     ax = plt.subplot(projection=wcs, slices=('x', 'y')) # RA on X axis, Dec on Y axis for the slice s
#     ax.imshow(image_data[s, :, :], cmap='viridis', norm=norm) #order of axis is reversed???

#     ra = ax.coords[0]
#     dec = ax.coords[1]

#     ra.set_axislabel('Right Ascension')
#     dec.set_axislabel('Declination')
    
#     # =====================================================================
#     # plt.savefig('zsqrt_slice%s_seg001_nrcb1.png' % s)
#     # Save the plot as PNG
#     output_filename = Path(filename).stem + f'_slice{int(s)+1}.png'
#     output_path = output_dir / output_filename
#     plt.savefig(output_path)
#     plt.close()  # Close the figure to release memory
#     return output_path


# def convertToPNG(theSlice, filepath, output_dir):
#     s = theSlice
#     number_size = 12
#     label_size = 20
#     with fits.open(filepath) as hdul:
#         hdu      = hdul[1]
#         data     = hdu.data[theSlice]                 # slice 50
#         orig_wcs = WCS(hdu.header, naxis=2).celestial

#     # 2) Build a new header where the CD matrix is purely diagonal:
#     new_hdr = hdu.header.copy()

#     # =============================================================
#     # original XY shape
#     ny, nx = data.shape

#     # compute a big enough square to hold the rotated image
#     diag = int(np.hypot(ny, nx))
#     new_hdr['NAXIS1'] = diag
#     new_hdr['NAXIS2'] = diag
#     # recenter CRPIX so your image sits in the middle of that big square:
#     new_hdr['CRPIX1'] = diag/2 + 0.5
#     new_hdr['CRPIX2'] = diag/2 + 0.5

#     # =============================================================
#     # zero‐rotation CD as before
#     # compute the pixel scale in degrees/pix
#     pixscale = proj_plane_pixel_scales(orig_wcs)
#     # zero out any rotation
#     new_hdr['CD1_1'], new_hdr['CD1_2'] = -pixscale[0], 0.0
#     new_hdr['CD2_1'], new_hdr['CD2_2'] =   0.0,        pixscale[1]
#     new_wcs = WCS(new_hdr, naxis=2).celestial

#     # 3) Reproject your slice onto that “north‐up, east‐right” WCS
#     # array, footprint = reproject_exact(
#     #     (data, orig_wcs),
#     #     new_wcs,
#     #     shape_out=data.shape
#     # )
#     array, footprint = reproject_interp(
#         (data, orig_wcs),
#         new_wcs,
#         shape_out=(diag, diag),
#         order=0                # 0 = nearest‐neighbor, 1 = linear (default)
#     )

#     # 4) Now plot with WCSAxes—axes will be straight
#     norm = ImageNormalize(array, interval=ZScaleInterval(), stretch=LinearStretch())

#     fig = plt.figure(figsize=(10,8))
#     ax  = fig.add_subplot(1,1,1, projection=new_wcs)

#     im = ax.imshow(array, origin='lower', cmap='viridis', norm=norm)

#     # grid + ticks on straight RA/Dec
#     ra = ax.coords['ra']
#     dec = ax.coords['dec']
#     ra.grid(color='lightgray', linestyle='solid')
#     dec.grid(color='black',    linestyle='solid')
#     ra.set_axislabel('Right Ascension', color='black', fontsize=label_size, minpad=0.8)
#     dec.set_axislabel('Declination', color='black', fontsize=label_size, minpad=0.5)
#     ra.set_ticks(number=10)
#     dec.set_ticks(number=10)
#     ra.set_ticklabel(size=number_size)
#     dec.set_ticklabel(size=number_size)
#     ra.set_major_formatter('hh:mm:ss.s')
#     dec.set_major_formatter('dd:mm:ss')

#     # plt.colorbar(im, ax=ax, label='Flux')
#     cbar = plt.colorbar(im,
#                     ax=ax,
#                     label='Flux',
#                     shrink=0.9,
#                     aspect=25,
#                     pad=0.04)
#     cbar.ax.tick_params(labelsize=number_size)
#     cbar.ax.yaxis.label.set_size(label_size)
    
#     # =====================================================================
#     # plt.savefig('zsqrt_slice%s_seg001_nrcb1.png' % s)
#     # Save the plot as PNG
#     output_filename = Path(filename).stem + f'_slice{int(s)+1}.png'
#     output_path = output_dir / output_filename
#     plt.savefig(output_path)
#     plt.close()  # Close the figure to release memory
#     return output_path

# def convertToPNG_forGroupImg(theSlice, filepath, output_dir):
#     s = theSlice
#     # Load the FITS data
#     with fits.open(filepath) as hdul:
#         data = hdul[1].data          # assumes your image lives in extension 1

#     # Extract the requested slice
#     img_slice = data[s, :, :]

#     # Auto-scale with zscale
#     norm = ImageNormalize(img_slice, interval=ZScaleInterval())

#     # Plot only the image, no axes
#     fig, ax = plt.subplots(figsize=(8, 8))
#     ax.imshow(img_slice, cmap='viridis', norm=norm)
#     ax.axis('off')   # <-- turns off x/y ticks and labels

#     # Save
#     # =====================================================================
#     # plt.savefig('zsqrt_slice%s_seg001_nrcb1.png' % s)
#     # Save the plot as PNG
#     output_filename = Path(filename).stem + f'_slice{int(s)+1}.png'
#     output_path = output_dir / output_filename
#     fig.tight_layout(pad=0)
#     fig.savefig(output_path, dpi=300, bbox_inches='tight', pad_inches=0)
#     plt.close(fig)
#     # =====================================================================
#     return output_path

# # Function to create a thumbnail from a PNG image
# def create_thumbnail(image_path, thumbnail_dir, size=(128, 128)):
#     img = Image.open(image_path)
#     img.thumbnail(size)
#     thumbnail_path = thumbnail_dir / image_path.name
#     img.save(thumbnail_path, "PNG")


# def convertToPNGWithAnnulus(
#     theSlice: int,
#     filepath: Path,
#     rawdata: dict,
#     # center_pix_orig: Optional[Sequence[float]] = None,
#     center_sky: Optional[SkyCoord] = None,
#     # ...OR pass a single list of (r_in, r_out) pairs:
#     radii_pairs: Optional[Sequence[Tuple[float, float]]] = None,
#     show_fill: bool = False,
#     output_dir: Union[str, Path] = ".",
#     isLabel: bool = False,
# ) -> List[Path]:
#     output_dir = Path(output_dir)
#     output_dir.mkdir(parents=True, exist_ok=True)

#     s = theSlice
#     filename = filepath.name
#     number_size = 12
#     label_size  = 20
#     label_ring_size  = 12
#     # --- ring-top labels ---
#     label_offset_px = 2
#     # fmt = lambda v: f"{v:.1f}"
#         # ---- Load & WCS setup ----
#         # ---- Load & WCS setup ----
#     with fits.open(filepath) as hdul:
#         hdu      = hdul[1]
#         data     = hdu.data[theSlice]
#         orig_wcs = WCS(hdu.header, naxis=2).celestial

#         # Build a new diagonal-CD header (north-up, east-right) with large enough canvas
#         ny, nx = data.shape
#         diag = int(np.hypot(ny, nx))

#         new_hdr = hdu.header.copy()
#         new_hdr['NAXIS1'] = diag
#         new_hdr['NAXIS2'] = diag
#         new_hdr['CRPIX1'] = diag/2 + 0.5
#         new_hdr['CRPIX2'] = diag/2 + 0.5

#         pixscale = proj_plane_pixel_scales(orig_wcs)
#         new_hdr['CD1_1'], new_hdr['CD1_2'] = -pixscale[0], 0.0
#         new_hdr['CD2_1'], new_hdr['CD2_2'] =  0.0,         pixscale[1]
#         new_wcs = WCS(new_hdr, naxis=2).celestial

#         # Reproject once
#         array, footprint = reproject_interp(
#             (data, orig_wcs), new_wcs, shape_out=(diag, diag), order=0
#         )



#     saved_paths: List[Path] = []

#     # Helper to render and save a figure (optionally with one annulus)
#     def render_and_save(
#         out_dir: Path,
#         center_pix_orig: (float, float)=None,
#         base_stem: str ="",
#         annulus: Optional[Tuple[float, float]] = None,
#         isLabel: bool = False,
#     ) -> Path:
#         xy_disp = None
#         if center_pix_orig is not None:
#             x0, y0 = float(center_pix_orig[0]), float(center_pix_orig[1])
#             sky = orig_wcs.pixel_to_world(x0, y0)
#             x1, y1 = new_wcs.world_to_pixel(sky)
#             xy_disp = (float(x1), float(y1))
#         elif center_sky is not None:
#             x1, y1 = new_wcs.world_to_pixel(center_sky)
#             xy_disp = (float(x1), float(y1))
#         norm = ImageNormalize(array, interval=ZScaleInterval(), stretch=LinearStretch())
#         fig = plt.figure(figsize=(10, 8))
#         ax  = fig.add_subplot(1, 1, 1, projection=new_wcs)

#         im = ax.imshow(array, origin='lower', cmap='viridis', norm=norm)

#         # WCS grid and labels
#         ra = ax.coords['ra']; dec = ax.coords['dec']
#         ra.grid(color='lightgray', linestyle='solid')
#         dec.grid(color='black', linestyle='solid')
#         ra.set_axislabel('Right Ascension', color='black', fontsize=label_size, minpad=0.8)
#         dec.set_axislabel('Declination', color='black', fontsize=label_size, minpad=0.5)
#         ra.set_ticks(number=10)
#         dec.set_ticks(number=10)
#         ra.set_ticklabel(size=number_size)
#         dec.set_ticklabel(size=number_size)
#         ra.set_major_formatter('hh:mm:ss.s')
#         dec.set_major_formatter('dd:mm:ss')

#         cbar = plt.colorbar(im, ax=ax, label='Flux', shrink=0.9, aspect=25, pad=0.04)
#         cbar.ax.tick_params(labelsize=number_size)
#         cbar.ax.yaxis.label.set_size(label_size)

#         # Draw annulus if requested and center is available
#         if annulus is not None and xy_disp is not None:
#             rin, rout = annulus
#             x, y = xy_disp

#             # # Star marker at displayed pixels
#             # ax.plot(x, y, marker='+', markersize=12, mew=2, color='white',
#             #         transform=ax.get_transform('pixel'), zorder=5)
            
#             # outer ring
#             outer = Circle((x, y), rout, fill=False, linewidth=1.8,
#                            edgecolor='white', alpha=0.95,
#                            transform=ax.get_transform('pixel'), zorder=5)
#             ax.add_patch(outer)
#             # inner ring
#             inner = Circle((x, y), rin, fill=False, linewidth=1.2,
#                            edgecolor='white', alpha=0.95, linestyle='--',
#                            transform=ax.get_transform('pixel'), zorder=5)
#             ax.add_patch(inner)

#             if show_fill and rout > rin:
#                 # optional faint fill of the annulus area
#                 fill = Circle((x, y), rout, fill=True, linewidth=0,
#                               alpha=0.08, transform=ax.get_transform('pixel'), zorder=4)
#                 ax.add_patch(fill)
#                 hole = Circle((x, y), rin, fill=True, color='black', linewidth=0,
#                               transform=ax.get_transform('pixel'), zorder=5)
#                 ax.add_patch(hole)
            
#             if isLabel:
#                 # white text with a thin black halo for readability
#                 text_kw = dict(
#                     transform=ax.get_transform('pixel'),
#                     ha='center', va='bottom',
#                     fontsize=label_ring_size, color='white', zorder=6,
#                     path_effects=[pe.Stroke(linewidth=2.5, foreground='black'), pe.Normal()],
#                 )

#                 # inner ring label at top of inner circle
#                 ax.text(x, y + rin + label_offset_px,
#                         f"r_in = {rin}", **text_kw)

#                 # outer ring label at top of outer circle
#                 ax.text(x, y + rout + label_offset_px,
#                         f"r_out = {rout}", **text_kw)

#             suffix = f"_rin{int(round(rin))}_rout{int(round(rout))}_label" if isLabel else f"_rin{int(round(rin))}_rout{int(round(rout))}"
#         else:
#             suffix = ""

#         out_name = f"{base_stem}{suffix}.png"
#         out_path = out_dir / out_name
#         plt.savefig(out_path, dpi=300, bbox_inches='tight')
#         plt.close(fig)
#         return out_path

#     base_stem = f"{Path(filename).stem}_slice{s+1}"

#     # Center known -> for each pair, save a separate PNG in output_annulus_dir
#     if not radii_pairs:
#         # If no pairs, just save base (centered) image (no annulus)
#         saved_paths.append(render_and_save(output_dir, None, base_stem, annulus=None))
#         return saved_paths

#     saved_paths.append(render_and_save(output_dir, None, base_stem, annulus=None))
#     for pair in radii_pairs:
#         r_in, r_out = pair
#         center_pix_orig = rawdata[r_in][r_out][filename][str(s+1)]
#         saved_paths.append(render_and_save(output_dir, center_pix_orig, base_stem, annulus=pair, isLabel=isLabel))

#     return saved_paths


# def process_data(collection_name):
#     rawdata = {}

#     print("Fetching data from MongoDB")
#     # db = get_db("jwst")
    
#     client = MongoClient(config.MONGO_LOCAL_URI)
#     db = client["jwst"]

#     collection = db[collection_name]
#     epochs = collection.distinct('epoch')

#     for epoch in epochs:
#         if epoch not in rawdata:
#             rawdata[epoch] = {}

#         types = collection.distinct('type', {'epoch': epoch})
#         for wave_type in types:
#             if wave_type not in rawdata[epoch]:
#                 rawdata[epoch][wave_type] = {}
#             r_in_values = collection.distinct(
#                 'r_in', {'epoch': epoch, 'type': wave_type})
#             for r_in in r_in_values:
#                 if r_in not in rawdata[epoch][wave_type]:
#                     rawdata[epoch][wave_type][r_in] = {}

#                 r_out_values = collection.distinct(
#                     'r_out', {'epoch': epoch, 'type': wave_type, 'r_in': r_in})
#                 for r_out in r_out_values:
#                     if r_out not in rawdata[epoch][wave_type][r_in]:
#                         rawdata[epoch][wave_type][r_in][r_out] = {}

#                         cursor = collection.find(
#                             {'epoch': epoch, 'type': wave_type, 'r_in': r_in, 'r_out': r_out})
#                         for doc in cursor:
#                             if 'aperture' in doc:
#                                 frames   = np.array(doc['aperture']['frame'])
#                                 filenames= np.array(doc['aperture']['filename'])
#                                 xcenters = np.array(doc['aperture']['xcenter'])
#                                 ycenters = np.array(doc['aperture']['ycenter'])

#                                 rawdata.setdefault(epoch, {}) \
#                                     .setdefault(wave_type, {}) \
#                                     .setdefault(r_in, {}) \
#                                     .setdefault(r_out, {})

#                                 target = rawdata[epoch][wave_type][r_in][r_out]

#                                 for fn, fr, x, y in zip(filenames, frames, xcenters, ycenters):
#                                     fn = str(fn)         # dict keys as strings (JSON-safe)
#                                     fr = str(fr)         # ditto; use int(fr) if you truly want int keys
#                                     xy = (float(x), float(y))

#                                     if fn not in target:
#                                         target[fn] = {}
#                                     target[fn][fr] = xy

#     return rawdata

# def _worker_convert(filename, frame_idx, output_dir, rawdata_subdict, radii_pairs, isLabel):
#     try:
#         import matplotlib
#         matplotlib.use("Agg")  # safe for parallel, headless
#         # Call your existing function. Make sure it opens/reads from `filepath` internally.
#         out_path = convertToPNGWithAnnulus(
#             theSlice=frame_idx,
#             filepath=Path(filename),
#             rawdata=rawdata_subdict,
#             radii_pairs=radii_pairs,          # full list, not a single pair
#             output_dir=Path(output_dir),
#             isLabel=isLabel,
#         )
#         return {"ok": True, "file": filename, "frame": frame_idx, "out": str(out_path)}
#     except Exception as e:
#         return {
#             "ok": False,
#             "file": filename,
#             "frame": frame_idx,
#             "err": f"{e.__class__.__name__}: {e}",
#             "trace": traceback.format_exc()
#         }
    
# def main():
#     rawdata = process_data('ZTF_J1539')   # runs ONCE in the main process

#     log_path = full_size_dir / "errors.txt"
#     log_path.parent.mkdir(parents=True, exist_ok=True)
#     with open(log_path, "w", encoding="utf-8") as f:
#         f.write("file\tframe\terror\ttraceback_last_line\n")

#     tasks = []
#     # for epoch in ["epoch1"]:
#     #     for wave_type in ["sw"]:
#     for epoch in ["epoch1", "epoch2"]:
#         for wave_type in ["lw", "sw"]:
#             if epoch == "epoch1":
#                 sw_files = sorted(original_path.glob("jw01666001001*_nrcb1/*crfints.fits"))
#                 lw_files = sorted(original_path.glob("jw01666001001*_nrcblong/*crfints.fits"))
#             else:
#                 sw_files = sorted(original_path.glob("jw01666003001*_nrcb1/*crfints.fits"))
#                 lw_files = sorted(original_path.glob("jw01666003001*_nrcblong/*crfints.fits"))

#             fileList = lw_files if wave_type == "lw" else sw_files

#             radii_pairs = [
#                 (float(r_in), float(r_out))
#                 for r_in, r_outs in rawdata[epoch][wave_type].items()
#                 for r_out in r_outs.keys()
#             ]

#             group_out_dir = full_size_dir / epoch / wave_type
#             group_out_dir.mkdir(parents=True, exist_ok=True)

#             for filename in fileList:
#                 try:
#                     with fits.open(filename, memmap=True) as f:
#                         data = f["SCI"].data
#                         nframes = data.shape[0] if data.ndim == 3 else 1
#                 except Exception as e:
#                     with open(log_path, "a", encoding="utf-8") as logf:
#                         logf.write(f"{filename}\t-1\tOpenError: {e}\n")
#                     continue

#                 # for i in range(0, 1):
#                 for i in range(0, nframes):
#                     tasks.append((
#                         str(filename), i, str(group_out_dir),
#                         rawdata[epoch][wave_type], radii_pairs, True
#                     ))
#                     tasks.append((
#                         str(filename), i, str(group_out_dir),
#                         rawdata[epoch][wave_type], radii_pairs, False
#                     ))
#     # Parallel execution
#     # max_workers = max(1, (os.cpu_count() or 4) - 1)
#     max_workers = 8
#     print(f"\nSubmitting {len(tasks)} tasks with {max_workers} workers...")

#     done, total = 0, len(tasks)
#     with ProcessPoolExecutor(max_workers=max_workers) as ex:
#         futs = [ex.submit(_worker_convert, *t) for t in tasks]
#         for fut in as_completed(futs):
#             res = fut.result()
#             done += 1
#             if not res["ok"]:
#                 last_line = res.get("trace", "").splitlines()[-1] if res.get("trace") else ""
#                 with open(log_path, "a", encoding="utf-8") as logf:
#                     logf.write(f"{res['file']}\t{res['frame']}\t{res['err']}\t{last_line}\n")
#             elif done % 10 == 0:
#                 print(f"Completed {done}/{total}")
#     print("\nAll submitted frames processed. See error log at:", log_path)
# if __name__ == "__main__":
#     mp.freeze_support()  # Windows safety
#     main()



# # # --- build tasks and run ---
# # rawdata = process_data('ZTF_J1539')

# # log_path = full_size_dir / "errors.txt"
# # log_path.parent.mkdir(parents=True, exist_ok=True)
# # with open(log_path, "w", encoding="utf-8") as f:
# #     f.write("file\tframe\terror\ttraceback_last_line\n")

# # tasks = []

# # for epoch in ["epoch1"]:
# #     for wave_type in ["sw"]:
# # # for epoch in ["epoch1", "epoch2"]:
# # #     for wave_type in ["lw", "sw"]:
# #         if epoch == "epoch1":
# #             sw_files = sorted(original_path.glob("jw01666001001*_nrcb1/*crfints.fits"))
# #             lw_files = sorted(original_path.glob("jw01666001001*_nrcblong/*crfints.fits"))
# #         else:
# #             sw_files = sorted(original_path.glob("jw01666003001*_nrcb1/*crfints.fits"))
# #             lw_files = sorted(original_path.glob("jw01666003001*_nrcblong/*crfints.fits"))

# #         fileList = lw_files if wave_type == "lw" else sw_files

# #         # Build the full list of (r_in, r_out) pairs once per epoch/wave_type
# #         radii_pairs = [
# #             (float(r_in), float(r_out))
# #             for r_in, r_outs in rawdata[epoch][wave_type].items()
# #             for r_out in r_outs.keys()
# #         ]

# #         # Output dir per group
# #         group_out_dir = full_size_dir / epoch / wave_type
# #         group_out_dir.mkdir(parents=True, exist_ok=True)

# #         print(f"\n=== {epoch} / {wave_type} ===")
# #         print(f"Files: {len(fileList)}  |  radii_pairs: {len(radii_pairs)}")

# #         for filename in fileList:
# #             print(f"Indexing frames in {filename} ...")
# #             try:
# #                 with fits.open(filename, memmap=True) as f:
# #                     data = f["SCI"].data
# #                     nframes = data.shape[0] if data.ndim == 3 else 1
# #             except Exception as e:
# #                 # Log open/read error immediately
# #                 with open(log_path, "a", encoding="utf-8") as logf:
# #                     logf.write(f"{filename}\t-1\tOpenError: {e}\t\n")
# #                 continue

# #             # IMPORTANT: use range(0, nframes) — not nframes+1
# #             for i in range(0, 1):
# #             # for i in range(0, nframes):
# #                 tasks.append((
# #                     str(filename),
# #                     i,
# #                     str(group_out_dir),
# #                     rawdata[epoch][wave_type],
# #                     radii_pairs
# #                 ))

# # # Parallel execution
# # # max_workers = max(1, (os.cpu_count() or 4) - 1)
# # max_workers = 8
# # print(f"\nSubmitting {len(tasks)} tasks with {max_workers} workers...")

# # done = 0
# # N = 10 # update progress every N completed tasks
# # with ProcessPoolExecutor(max_workers=max_workers) as ex:
# #     futs = [ex.submit(_worker_convert, *t) for t in tasks]
# #     for fut in as_completed(futs):
# #         res = fut.result()
# #         done += 1
# #         if res["ok"]:
# #             if done % N == 0:
# #                 print(f"Completed {done}/{len(tasks)}")
# #         else:
# #             last_line = res.get("trace", "").splitlines()[-1] if res.get("trace") else ""
# #             with open(log_path, "a", encoding="utf-8") as logf:
# #                 logf.write(f"{res['file']}\t{res['frame']}\t{res['err']}\t{last_line}\n")

# # print("\nAll submitted frames processed. See error log at:", log_path)

# # # print(rawdata)
# # for epoch in ["epoch1","epoch2"]:
# #     # for wave_type in ["sw"]:
# #     for wave_type in ["lw", "sw"]:
# #         if epoch == "epoch1":
# #             sw_files = sorted(original_path.glob("jw01666001001*_nrcb1/*crfints.fits"))
# #             lw_files = sorted(original_path.glob("jw01666001001*_nrcblong/*crfints.fits"))
# #         else:
# #             sw_files = sorted(original_path.glob("jw01666003001*_nrcb1/*crfints.fits"))
# #             lw_files = sorted(original_path.glob("jw01666003001*_nrcblong/*crfints.fits"))

# #         fileList = lw_files
# #         if wave_type == "sw":
# #             fileList = sw_files
# #         radii_pairs = []
# #         for r_in in rawdata[epoch][wave_type]:
# #             for r_out in rawdata[epoch][wave_type][r_in]:
# #                 radii_pairs.append((r_in, r_out))
# #         for filename in fileList:
# #             print(f"Processing {filename}...")
# #             f = fits.open(filename)
# #             data = f["SCI"]
            
# #             istart = 0  # there is no source in first few frames, this *could* cause a problem. Include them for now.
# #             iend = data.data.shape[0]    

# #             # for i in range(0,1):
# #             for i in range(istart, iend+1):
# #                 print("File: ",filename ," Frame: ", i+1)
# #                 # OnlyImg_output_dir = OnlyImg_dir/ epoch/ wave_type
# #                 # OnlyImg_output_dir.mkdir(parents=True, exist_ok=True)
# #                 # thumbnail_OnlyImg_dir = thumbnail_OnlyImg_dir/ epoch/ wave_type
# #                 # thumbnail_OnlyImg_dir.mkdir(parents=True, exist_ok=True)
# #                 full_size_output_dir = full_size_dir/ epoch/ wave_type
# #                 full_size_output_dir.mkdir(parents=True, exist_ok=True)
# #                 # zoom_output_dir = zoom_dir/ epoch/ wave_type
# #                 # zoom_output_dir.mkdir(parents=True, exist_ok=True)
# #                 # thumbnail_output_dir = thumbnail_dir/ epoch/ wave_type
# #                 # thumbnail_output_dir.mkdir(parents=True, exist_ok=True)
# #                 try:
# #                     # output_path = convertToPNG_forGroupImg(i, filename, OnlyImg_output_dir)
# #                     output_path = convertToPNGWithAnnulus(theSlice=i, filepath=filename, rawdata=rawdata[epoch][wave_type], radii_pairs=[(r_in, r_out)], output_dir=full_size_output_dir)
# #                     # output_path = convertToPNG(i, filename, zoom_output_dir)
# #                     # # Create a thumbnail of the saved PNG
# #                     # create_thumbnail(output_path, thumbnail_output_dir)
# #                     # create_thumbnail(output_path, thumbnail_OnlyImg_dir)
# #                 except Exception as e:
# #                     print("Error: ", filename)
# #                     print("iend: ", iend)
# #                     print(e)
# #                     print("----------------------------------------------------------------------------------------------------------------------")
            
# #             f.close()
# #             print(f"Finished {filename}...")
# #             print("===========================================================================================================================")

# # print("Conversion completed.")
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
from pymongo import MongoClient
from typing import Sequence, Tuple, Optional, List, Union
import matplotlib.patheffects as pe
import json, gzip
from typing import Dict, Any, Union
import warnings
from astropy.wcs import FITSFixedWarning
warnings.filterwarnings('ignore', category=FITSFixedWarning)

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from astropy.io import fits
from astropy.wcs import WCS
from astropy.visualization import ZScaleInterval, ImageNormalize, LinearStretch
from astropy.wcs.utils import proj_plane_pixel_scales
from astropy.coordinates import SkyCoord
from reproject import reproject_interp

from concurrent.futures import ProcessPoolExecutor, as_completed
from astropy.io import fits
from pathlib import Path
import os, traceback

import os, traceback, multiprocessing as mp
import subprocess, os
from pathlib import Path
from fnmatch import fnmatch

# Set the original path for FITS files
# original_path = Path(r"/mnt/VIZ/work/proemsri/jwst/MAST_2023-10-07T0548/JWST")
original_path = Path(r"T:\JWST-Timing\MAST_2023-10-07T0548\JWST")
# git_dir = Path(r"/mnt/VIZ/work/proemsri/jwst/jwst-data")
# Set the output directories for full-size images and thumbnails
# full_size_dir = Path(r"/mnt/VIZ/work/proemsri/jwst/jwst-data/img/full-size/ZTF_J1539")

full_size_dir = Path(r"T:\JWST-Timing\jwst\output\test")
full_size_dir.mkdir(parents=True, exist_ok=True)

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
    output_filename = Path(filepath).stem + f'_slice{int(s)+1}.png'
    output_path = output_dir / output_filename
    plt.savefig(output_path)
    plt.close()  # Close the figure to release memory
    return output_path


def convertToPNGWithAnnulus(
    theSlice: int,
    filepath: Path,
    rawdata: dict,
    # center_pix_orig: Optional[Sequence[float]] = None,
    center_sky: Optional[SkyCoord] = None,
    # ...OR pass a single list of (r_in, r_out) pairs:
    radii_pairs: Optional[Sequence[Tuple[float, float]]] = None,
    show_fill: bool = False,
    output_dir: Union[str, Path] = ".",
    isLabel: bool = False,
) -> List[Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    s = theSlice
    filename = filepath.name
    number_size = 12
    label_size  = 20
    label_ring_size  = 12
    # --- ring-top labels ---
    label_offset_px = 2
    # fmt = lambda v: f"{v:.1f}"
        # ---- Load & WCS setup ----
    with fits.open(filepath) as hdul:
        hdu      = hdul[1]
        data     = hdu.data[theSlice]
        orig_wcs = WCS(hdu.header, naxis=2).celestial

        # Build a new diagonal-CD header (north-up, east-right) with large enough canvas
        ny, nx = data.shape
        diag = int(np.hypot(ny, nx))

        new_hdr = hdu.header.copy()
        new_hdr['NAXIS1'] = diag
        new_hdr['NAXIS2'] = diag
        new_hdr['CRPIX1'] = diag/2 + 0.5
        new_hdr['CRPIX2'] = diag/2 + 0.5

        pixscale = proj_plane_pixel_scales(orig_wcs)
        new_hdr['CD1_1'], new_hdr['CD1_2'] = -pixscale[0], 0.0
        new_hdr['CD2_1'], new_hdr['CD2_2'] =  0.0,         pixscale[1]
        new_wcs = WCS(new_hdr, naxis=2).celestial

        # Reproject once
        array, footprint = reproject_interp(
            (data, orig_wcs), new_wcs, shape_out=(diag, diag), order=0
        )



    saved_paths: List[Path] = []

    # Helper to render and save a figure (optionally with one annulus)
    def render_and_save(
        out_dir: Path,
        center_pix_orig: (float, float)=None,
        base_stem: str ="",
        annulus: Optional[Tuple[float, float]] = None,
        isLabel: bool = False,
    ) -> Path:
        xy_disp = None
        if center_pix_orig is not None:
            x0, y0 = float(center_pix_orig[0]), float(center_pix_orig[1])
            sky = orig_wcs.pixel_to_world(x0, y0)
            x1, y1 = new_wcs.world_to_pixel(sky)
            xy_disp = (float(x1), float(y1))
        elif center_sky is not None:
            x1, y1 = new_wcs.world_to_pixel(center_sky)
            xy_disp = (float(x1), float(y1))
        norm = ImageNormalize(array, interval=ZScaleInterval(), stretch=LinearStretch())
        fig = plt.figure(figsize=(10, 8))
        ax  = fig.add_subplot(1, 1, 1, projection=new_wcs)

        im = ax.imshow(array, origin='lower', cmap='viridis', norm=norm)

        # WCS grid and labels
        ra = ax.coords['ra']; dec = ax.coords['dec']
        ra.grid(color='lightgray', linestyle='solid')
        dec.grid(color='black', linestyle='solid')
        ra.set_axislabel('Right Ascension', color='black', fontsize=label_size, minpad=0.8)
        dec.set_axislabel('Declination', color='black', fontsize=label_size, minpad=0.5)
        ra.set_ticks(number=10)
        dec.set_ticks(number=10)
        ra.set_ticklabel(size=number_size)
        dec.set_ticklabel(size=number_size)
        ra.set_major_formatter('hh:mm:ss.s')
        dec.set_major_formatter('dd:mm:ss')

        cbar = plt.colorbar(im, ax=ax, label='Flux', shrink=0.9, aspect=25, pad=0.04)
        cbar.ax.tick_params(labelsize=number_size)
        cbar.ax.yaxis.label.set_size(label_size)

        # Draw annulus if requested and center is available
        if annulus is not None and xy_disp is not None:
            rin, rout = annulus
            x, y = xy_disp

            # # Star marker at displayed pixels
            # ax.plot(x, y, marker='+', markersize=12, mew=2, color='white',
            #         transform=ax.get_transform('pixel'), zorder=5)
            
            # outer ring
            outer = Circle((x, y), rout, fill=False, linewidth=1.8,
                           edgecolor='white', alpha=0.95,
                           transform=ax.get_transform('pixel'), zorder=5)
            ax.add_patch(outer)
            # inner ring
            inner = Circle((x, y), rin, fill=False, linewidth=1.2,
                           edgecolor='white', alpha=0.95, linestyle='--',
                           transform=ax.get_transform('pixel'), zorder=5)
            ax.add_patch(inner)

            if show_fill and rout > rin:
                # optional faint fill of the annulus area
                fill = Circle((x, y), rout, fill=True, linewidth=0,
                              alpha=0.08, transform=ax.get_transform('pixel'), zorder=4)
                ax.add_patch(fill)
                hole = Circle((x, y), rin, fill=True, color='black', linewidth=0,
                              transform=ax.get_transform('pixel'), zorder=5)
                ax.add_patch(hole)
            
            if isLabel:
                # white text with a thin black halo for readability
                text_kw = dict(
                    transform=ax.get_transform('pixel'),
                    ha='center', va='bottom',
                    fontsize=label_ring_size, color='white', zorder=6,
                    path_effects=[pe.Stroke(linewidth=2.5, foreground='black'), pe.Normal()],
                )

                # inner ring label at top of inner circle
                ax.text(x, y + rin + label_offset_px,
                        f"r_in = {rin}", **text_kw)

                # outer ring label at top of outer circle
                ax.text(x, y + rout + label_offset_px,
                        f"r_out = {rout}", **text_kw)

            suffix = f"_rin{int(round(rin))}_rout{int(round(rout))}_label" if isLabel else f"_rin{int(round(rin))}_rout{int(round(rout))}"
        else:
            suffix = ""

        out_name = f"{base_stem}{suffix}.png"
        out_path = out_dir / out_name
        plt.savefig(out_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        return out_path

    base_stem = f"{Path(filename).stem}_slice{s+1}"

    # Center known -> for each pair, save a separate PNG in output_annulus_dir
    if not radii_pairs:
        # If no pairs, just save base (centered) image (no annulus)
        saved_paths.append(render_and_save(output_dir, None, base_stem, annulus=None))
        return saved_paths

    saved_paths.append(render_and_save(output_dir, None, base_stem, annulus=None))
    for r_in_key, r_out_key in radii_pairs:
        # center lookups use string keys
        frames_map = rawdata.get(r_in_key, {}).get(r_out_key, {}).get(filename, {})
        center_pix_orig = frames_map.get(str(s+1))
        if center_pix_orig is None:
            # no center for this file+frame+ring; skip gracefully
            continue

        # draw with numeric radii
        r_in  = float(r_in_key)
        r_out = float(r_out_key)
        saved_paths.append(
            render_and_save(output_dir, center_pix_orig, base_stem,
                            annulus=(r_in, r_out), isLabel=isLabel)
    )

    return saved_paths

def convertImgToJSON(
    theSlice,
    filepath,
    rawdata: dict,
    # center_pix_orig=None,
    # center_sky: SkyCoord=None,
    radii_pairs=None,
    n_grid=10,
    # save_json_path="output.json",
    output_dir: Union[str, Path] = ".",
) -> List[Path]:
    """
    Export JWST FITS slice into a JSON file containing:
    - Rotated/north-up image
    - ZScale normalization
    - Full WCS metadata
    - RA/Dec grid lines (pixel coords)
    - RA/Dec tick labels (pixel coords)
    - Center pixel (optional)
    - Annulus radii (optional)
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    s = theSlice
    filename = filepath.name
    base_stem = f"{Path(filename).stem}_slice{s+1}"
    for r_in_key, r_out_key in radii_pairs:
        # center lookups use string keys
        frames_map = rawdata.get(r_in_key, {}).get(r_out_key, {}).get(filename, {})
        center_pix_orig = frames_map.get(str(s+1))
        if center_pix_orig is None:
            # no center for this file+frame+ring; skip gracefully
            continue
        else:
            break  # use the first available center
    # r_in_key, r_out_key = radii_pairs[0]
    # frames_map = rawdata.get(r_in_key, {}).get(r_out_key, {}).get(base_stem, {})
    # center_pix_orig = frames_map.get(str(s+1))
    output_filename = f"{base_stem}.json"
    output_path = output_dir / output_filename
    # ========== 1. Load slice ==========
    with fits.open(filepath) as hdul:
        hdu = hdul[1]
        data = hdu.data[s]
        orig_wcs = WCS(hdu.header, naxis=2).celestial

    ny, nx = data.shape
    diag = int(np.hypot(ny, nx))

    # ========== 2. Build north-up WCS ==========
    hdr = hdu.header.copy()
    hdr["NAXIS1"] = diag
    hdr["NAXIS2"] = diag
    hdr["CRPIX1"] = diag / 2 + 0.5
    hdr["CRPIX2"] = diag / 2 + 0.5

    pixscale = proj_plane_pixel_scales(orig_wcs)
    hdr["CD1_1"], hdr["CD1_2"] = -pixscale[0], 0.0
    hdr["CD2_1"], hdr["CD2_2"] = 0.0, pixscale[1]

    new_wcs = WCS(hdr, naxis=2).celestial

    # ========== 3. Reproject =============
    array, footprint = reproject_interp(
        (data, orig_wcs),
        new_wcs,
        shape_out=(diag, diag),
        order=0
    )

    # ========== 4. ZScale normalization ==========
    interval = ZScaleInterval()
    vmin, vmax = interval.get_limits(array)
    # norm = ImageNormalize(array, interval=ZScaleInterval(), stretch=LinearStretch())

    # ========== 5. Center pixel transform ==========
    xy_disp = None
    if center_pix_orig is not None:
        x0, y0 = float(center_pix_orig[0]), float(center_pix_orig[1])
        sky = orig_wcs.pixel_to_world(x0, y0)
        px, py = new_wcs.world_to_pixel(sky)
        xy_disp = (float(px), float(py))
    # elif center_sky is not None:
    #     px, py = new_wcs.world_to_pixel(center_sky)
    #     xy_disp = (float(px), float(py))

    # =====================================================
    # 6. Compute RA/Dec grid lines
    # =====================================================

    # determine RA/Dec bounds of the 4 corners
    H, W = diag, diag
    corners = np.array([
        [0, 0],
        [W - 1, 0],
        [0, H - 1],
        [W - 1, H - 1]
    ])
    sky = new_wcs.pixel_to_world(corners[:, 0], corners[:, 1])
    ra_vals = sky.ra.deg
    dec_vals = sky.dec.deg

    ra_min, ra_max = ra_vals.min(), ra_vals.max()
    dec_min, dec_max = dec_vals.min(), dec_vals.max()

    # evenly spaced grid
    ra_grid = np.linspace(ra_min, ra_max, n_grid)
    dec_grid = np.linspace(dec_min, dec_max, n_grid)

    # Sample functions
    def sample_constant_ra(ra_deg):
        # sample along dec direction
        decs = np.linspace(dec_min, dec_max, 300)
        world = SkyCoord(ra=ra_deg, dec=decs, unit="deg")
        px, py = new_wcs.world_to_pixel(world)
        pts = np.stack([px, py], axis=1)
        return pts.tolist()

    def sample_constant_dec(dec_deg):
        ras = np.linspace(ra_min, ra_max, 300)
        world = SkyCoord(ra=ras, dec=dec_deg, unit="deg")
        px, py = new_wcs.world_to_pixel(world)
        pts = np.stack([px, py], axis=1)
        return pts.tolist()

    # Grid lines
    ra_lines = [
        {
            "ra_deg": float(r),
            "pixels": sample_constant_ra(r)
        }
        for r in ra_grid
    ]

    dec_lines = [
        {
            "dec_deg": float(d),
            "pixels": sample_constant_dec(d)
        }
        for d in dec_grid
    ]

    # Tick labels
    def tick_ra(r):
        # pixel at bottom edge
        world = SkyCoord(ra=r, dec=dec_min, unit="deg")
        px, py = new_wcs.world_to_pixel(world)
        label = SkyCoord(ra=r, dec=0, unit="deg").ra.to_string(unit="hour", sep=":", precision=1)
        return {
            "px": [float(px), float(py)],
            "label": label
        }

    def tick_dec(d):
        world = SkyCoord(ra=ra_min, dec=d, unit="deg")
        px, py = new_wcs.world_to_pixel(world)
        label = SkyCoord(ra=0, dec=d, unit="deg").dec.to_string(unit="deg", sep=":", precision=1)
        return {
            "px": [float(px), float(py)],
            "label": label
        }

    ticks = {
        "ra": [tick_ra(r) for r in ra_grid],
        "dec": [tick_dec(d) for d in dec_grid]
    }
    # Convert to list and replace NaN/inf with None
    def sanitize(x):
        if isinstance(x, float) and (np.isnan(x) or np.isinf(x)):
            return None
        return x

    data_list = array.astype(np.float32).tolist()
    data_list = [[sanitize(v) for v in row] for row in data_list]
    # =====================================================
    # 7. Build JSON object
    # =====================================================
    result = {
        "meta": {
            "width": int(diag),
            "height": int(diag),
            "dtype": "float32_le",
            "order": "row-major",
            "norm": {
                "kind": "linear",
                "vmin": float(vmin),
                "vmax": float(vmax)
            },
            "crval": new_wcs.wcs.crval.tolist(),
            "crpix": new_wcs.wcs.crpix.tolist(),
            "cd": new_wcs.wcs.cd.tolist()
        },

        "data": data_list,

        "center": xy_disp,
        "radii_pairs": radii_pairs,

        "grid": {
            "ra_lines": ra_lines,
            "dec_lines": dec_lines,
            "ticks": ticks
        }
    }

    # Save JSON
    with open(output_path, "w") as f:
        json.dump(result, f)

    return output_path


def process_data(collection_name):
    rawdata = {}

    print("Fetching data from MongoDB")
    # db = get_db("jwst")
    
    client = MongoClient(config.MONGO_LOCAL_URI)
    db = client["jwst"]

    collection = db[collection_name]
    epochs = collection.distinct('epoch')

    for epoch in epochs:
        if epoch not in rawdata:
            rawdata[epoch] = {}

        types = collection.distinct('type', {'epoch': epoch})
        for wave_type in types:
            if wave_type not in rawdata[epoch]:
                rawdata[epoch][wave_type] = {}
            r_in_values = collection.distinct(
                'r_in', {'epoch': epoch, 'type': wave_type})
            for r_in in r_in_values:
                if r_in not in rawdata[epoch][wave_type]:
                    rawdata[epoch][wave_type][r_in] = {}

                r_out_values = collection.distinct(
                    'r_out', {'epoch': epoch, 'type': wave_type, 'r_in': r_in})
                for r_out in r_out_values:
                    if r_out not in rawdata[epoch][wave_type][r_in]:
                        rawdata[epoch][wave_type][r_in][r_out] = {}

                        cursor = collection.find(
                            {'epoch': epoch, 'type': wave_type, 'r_in': r_in, 'r_out': r_out})
                        for doc in cursor:
                            if 'aperture' in doc:
                                frames   = np.array(doc['aperture']['frame'])
                                filenames= np.array(doc['aperture']['filename'])
                                xcenters = np.array(doc['aperture']['xcenter'])
                                ycenters = np.array(doc['aperture']['ycenter'])

                                rawdata.setdefault(epoch, {}) \
                                    .setdefault(wave_type, {}) \
                                    .setdefault(r_in, {}) \
                                    .setdefault(r_out, {})

                                target = rawdata[epoch][wave_type][r_in][r_out]

                                for fn, fr, x, y in zip(filenames, frames, xcenters, ycenters):
                                    fn = str(fn)         # dict keys as strings (JSON-safe)
                                    fr = str(fr)         # ditto; use int(fr) if you truly want int keys
                                    xy = (float(x), float(y))

                                    if fn not in target:
                                        target[fn] = {}
                                    target[fn][fr] = xy

    return rawdata

def _worker_convert_Annulus(filename, frame_idx, output_dir, rawdata_subdict, radii_pairs, isLabel):
    try:
        import matplotlib
        matplotlib.use("Agg")  # safe for parallel, headless
        # Call your existing function. Make sure it opens/reads from `filepath` internally.
        out_path = convertToPNGWithAnnulus(
            theSlice=frame_idx,
            filepath=Path(filename),
            rawdata=rawdata_subdict,
            radii_pairs=radii_pairs,          # full list, not a single pair
            output_dir=Path(output_dir),
            isLabel=isLabel,
        )
        return {"ok": True, "file": filename, "frame": frame_idx, "out": str(out_path)}
    except Exception as e:
        return {
            "ok": False,
            "file": filename,
            "frame": frame_idx,
            "err": f"{e.__class__.__name__}: {e}",
            "trace": traceback.format_exc()
        }
def _worker_convert_normalImg(filename, frame_idx, output_dir):
    try:
        import matplotlib
        matplotlib.use("Agg")  # safe for parallel, headless
        out_path = convertToPNG(
            theSlice=frame_idx,
            filepath=Path(filename),
            output_dir=Path(output_dir)
        )
        return {"ok": True, "file": filename, "frame": frame_idx, "out": str(out_path)}
    except Exception as e:
        return {
            "ok": False,
            "file": filename,
            "frame": frame_idx,
            "err": f"{e.__class__.__name__}: {e}",
            "trace": traceback.format_exc()
        }

def _worker_convert_imgJson(filename, frame_idx, output_dir, rawdata_subdict, radii_pairs):
    try:
        import matplotlib
        matplotlib.use("Agg")  # safe for parallel, headless
        # Call your existing function. Make sure it opens/reads from `filepath` internally.
        out_path = convertImgToJSON(
            theSlice=frame_idx,
            filepath=Path(filename),
            rawdata=rawdata_subdict,
            radii_pairs=radii_pairs,          # full list, not a single pair
            n_grid=10,
            output_dir=Path(output_dir),
        )
        return {"ok": True, "file": filename, "frame": frame_idx, "out": str(out_path)}
    except Exception as e:
        return {
            "ok": False,
            "file": filename,
            "frame": frame_idx,
            "err": f"{e.__class__.__name__}: {e}",
            "trace": traceback.format_exc()
        }



def load_json(path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load JSON (supports .gz or plain .json).
    """
    path = Path(path)
    if path.suffix == ".gz":
        with gzip.open(path, "rt", encoding="utf-8") as f:
            return json.load(f)
    else:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)


def git_commit_push(target_dir: Path, message: str) -> bool:
    """
    Stage ONLY changes under target_dir, commit if there are staged changes,
    and push to the current branch. Returns True if a commit was made.
    """
    target_dir = Path(target_dir).resolve()

    # Ensure we're inside a git repo and find its root
    p = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=str(target_dir),
        capture_output=True, text=True
    )
    if p.returncode != 0:
        raise RuntimeError(f"{target_dir} is not inside a Git repository.")
    repo_root = Path(p.stdout.strip())

    # Stage changes only under target_dir (relative path from repo root)
    rel = os.path.relpath(str(target_dir), str(repo_root))
    subprocess.run(["git", "add", "-A", "--", rel], cwd=str(repo_root), check=True)

    # If nothing staged, skip commit
    # (git diff --cached --quiet returns 0 when no changes)
    diff = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=str(repo_root))
    if diff.returncode == 0:
        return False

    subprocess.run(["git", "commit", "-m", message], cwd=str(repo_root), check=True)
    # Push to the current checked-out branch
    subprocess.run(["git", "push", "-u", "origin", "HEAD"], cwd=str(repo_root), check=True)
    return True


from fnmatch import fnmatch

def git_push_in_batches_with_progress(target_dir: Path, message: str,
                                      batch_size: int = 100,
                                      patterns=("*.png",),
                                      pack_threads: int | None = 0) -> int:
    """
    Commit & push changed files under target_dir in batches, reporting 'X/Y'.
    Returns total files pushed. pack_threads=0 lets Git use all cores to pack.
    """
    target_dir = Path(target_dir).resolve()
    p = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                       cwd=str(target_dir), capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"{target_dir} is not inside a Git repository.")
    repo_root = Path(p.stdout.strip())
    rel = os.path.relpath(str(target_dir), str(repo_root))

    # list pending files once so we know the total
    p = subprocess.run(
        ["git", "ls-files", "--others", "--modified", "--exclude-standard", "--", rel],
        cwd=str(repo_root), capture_output=True, text=True, check=True
    )
    pending = [ln.strip() for ln in p.stdout.splitlines() if ln.strip()]
    pending = [f for f in pending if any(fnmatch(os.path.basename(f), pat) for pat in patterns)]
    total = len(pending)
    if total == 0:
        print("[git] Nothing to push.")
        return 0

    pushed = 0
    batch_no = 0
    while pending:
        batch_no += 1
        batch = pending[:batch_size]
        pending = pending[batch_size:]

        # unstage everything under target_dir; then stage only this batch
        subprocess.run(["git", "reset", "-q", "HEAD", "--", rel], cwd=str(repo_root))
        subprocess.run(["git", "add", "--"] + batch, cwd=str(repo_root), check=True)

        # commit if something is staged
        if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=str(repo_root)).returncode != 0:
            subprocess.run(["git", "commit",
                            "-m", f"{message} (+{len(batch)} files, batch {batch_no})"],
                           cwd=str(repo_root), check=True)
            push_cmd = ["git"]
            if pack_threads is not None:
                push_cmd += ["-c", f"pack.threads={pack_threads}"]  # 0 = all cores
            push_cmd += ["push", "origin", "HEAD"]
            subprocess.run(push_cmd, cwd=str(repo_root), check=True)

            pushed += len(batch)
            print(f"[git] {pushed}/{total} pushed (batch {batch_no}, +{len(batch)})")

    return pushed
# Helper function to run any task list
def run_tasks(name, task_list, worker_func, max_workers, log_path):
    if not task_list:
        print(f"[{name}] No tasks to run.")
        return

    print(f"\nSubmitting {len(task_list)} {name} tasks with {max_workers} workers...")
    done = 0
    total = len(task_list)

    with ProcessPoolExecutor(max_workers=max_workers) as ex:
        futures = [ex.submit(worker_func, *t) for t in task_list]

        for fut in as_completed(futures):
            res = fut.result()
            done += 1

            if not res["ok"]:
                last_line = res.get("trace", "").splitlines()[-1] if res.get("trace") else ""
                with open(log_path, "a", encoding="utf-8") as logf:
                    logf.write(f"{res['file']}\t{res['frame']}\t{res['err']}\t{last_line}\n")

            if done % 10 == 0 or done == total:
                print(f"[{name}] {done}/{total}")

    print(f"[{name}] COMPLETE.\n")
    print("----------------------------------------------------------------------------------------------")  # newline after the watch-style progress
    print("\n")
    print("\n")
    print("\n")


def main():
    rawdata = process_data('ZTF_J1539')
    # rawdata = load_json(r"/mnt/VIZ/work/proemsri/jwst/rawdata.json")
    # log_path = Path("/mnt/VIZ/work/proemsri/jwst/errors.txt")
    log_path = Path("T:\JWST-Timing\jwst\error\errors.txt")
    
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("file\tframe\terror\ttraceback_last_line\n")

    tasks_Annulus = []
    tasks_normalImg = []
    tasks_imgJson = []
    for epoch in ["epoch1"]:
        for wave_type in ["sw"]:
    # for epoch in ["epoch1", "epoch2"]:
    #     for wave_type in ["lw", "sw"]:
            if epoch == "epoch1":
                sw_files = sorted(original_path.glob("jw01666001001*_nrcb1/*crfints.fits"))
                lw_files = sorted(original_path.glob("jw01666001001*_nrcblong/*crfints.fits"))
            else:
                sw_files = sorted(original_path.glob("jw01666003001*_nrcb1/*crfints.fits"))
                lw_files = sorted(original_path.glob("jw01666003001*_nrcblong/*crfints.fits"))

            fileList = lw_files if wave_type == "lw" else sw_files

            radii_pairs = [
                (r_in_key, r_out_key)
                for r_in_key, r_outs in rawdata[epoch][wave_type].items()
                for r_out_key in r_outs.keys()
            ]

            group_out_dir = full_size_dir / epoch / wave_type
            group_out_dir.mkdir(parents=True, exist_ok=True)

            for filename in fileList:
                try:
                    with fits.open(filename, memmap=True) as f:
                        data = f["SCI"].data
                        nframes = data.shape[0] if data.ndim == 3 else 1
                except Exception as e:
                    with open(log_path, "a", encoding="utf-8") as logf:
                        logf.write(f"{filename}\t-1\tOpenError: {e}\n")
                    continue

                for i in range(0, 10):
                # for i in range(0, nframes):
                    # tasks_Annulus.append((
                    #     str(filename), i, str(group_out_dir),
                    #     rawdata[epoch][wave_type], radii_pairs, True
                    # ))
                    # tasks_Annulus.append((
                    #     str(filename), i, str(group_out_dir),
                    #     rawdata[epoch][wave_type], radii_pairs, False
                    # ))
                    tasks_normalImg.append((
                        str(filename), i, str(group_out_dir)
                    ))
                    tasks_imgJson.append((
                        str(filename), i, str(group_out_dir),
                        rawdata[epoch][wave_type], radii_pairs
                    ))
    # Parallel execution
    # max_workers = max(1, (os.cpu_count() or 4) - 1)
    max_workers = 16
    # -------------------------
    # RUN EACH GROUP
    # -------------------------
    # run_tasks("Annulus", tasks_Annulus, _worker_convert_Annulus, max_workers, log_path)
    run_tasks("NormalImg", tasks_normalImg, _worker_convert_normalImg, max_workers, log_path)
    run_tasks("ImgJSON", tasks_imgJson, _worker_convert_imgJson, max_workers, log_path)

    print("All tasks finished. Starting Git push…")

    # print(f"\nSubmitting {len(tasks_Annulus)} tasks with {max_workers} workers...")

    # done, total = 0, len(tasks_Annulus)
    # with ProcessPoolExecutor(max_workers=max_workers) as ex:
    #     futs = [ex.submit(_worker_convert_Annulus, *t) for t in tasks_Annulus]
    #     for fut in as_completed(futs):
    #         res = fut.result()
    #         done += 1

    #         if not res["ok"]:
    #             last_line = res.get("trace", "").splitlines()[-1] if res.get("trace") else ""
    #             with open(log_path, "a", encoding="utf-8") as logf:
    #                 logf.write(f"{res['file']}\t{res['frame']}\t{res['err']}\t{last_line}\n")

    #         # single-line progress like "10/5000"
    #         if done % 10 == 0 or done == total:
    #             print("===============================================================================================")
    #             print(f"\r{done}/{total}", end="", flush=True)
    # print("----------------------------------------------------------------------------------------------")  # newline after the watch-style progress
    # print("\n")
    # print("\n")
    # print("\n")
    # Push in batches of 500 AFTER the pool shuts down
    # -------------------------
    # GIT PUSH AFTER ALL TASKS
    # -------------------------
    # pushed = git_push_in_batches_with_progress(
    #     full_size_dir,
    #     message="Update images",
    #     batch_size=500,
    #     patterns=("*.png", "*.json", "*.json.gz"),
    #     pack_threads=0,   # let Git use all cores for packing
    # )
    # print(f"[git] pushed {pushed} files.")
    print("\nAll submitted frames processed. See error log at:", log_path)

if __name__ == "__main__":
    mp.freeze_support()  # Windows safety
    main()
