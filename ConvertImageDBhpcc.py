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
original_path = Path(r"/mnt/VIZ/work/proemsri/jwst/MAST_2023-10-07T0548/JWST")
git_dir = Path(r"/mnt/VIZ/work/proemsri/jwst/jwst-data")
# Set the output directories for full-size images and thumbnails
full_size_dir = Path(r"/mnt/VIZ/work/proemsri/jwst/jwst-data/img/full-size/ZTF_J1539")
full_size_dir.mkdir(parents=True, exist_ok=True)
json_img_dir = Path(r"/mnt/VIZ/work/proemsri/jwst/jwst-data/img/json/ZTF_J1539")
json_img_dir.mkdir(parents=True, exist_ok=True)


def convertToPNG(theSlice, filepath, output_dir, vmin=None, vmax=None):
    s = theSlice
    number_size = 12
    label_size = 20
    with fits.open(filepath) as hdul:
        hdu      = hdul[1]
        data     = hdu.data[theSlice]
        orig_wcs = WCS(hdu.header, naxis=2).celestial

    new_hdr = hdu.header.copy()
    ny, nx = data.shape
    diag = int(np.hypot(ny, nx))
    new_hdr['NAXIS1'] = diag
    new_hdr['NAXIS2'] = diag
    new_hdr['CRPIX1'] = diag/2 + 0.5
    new_hdr['CRPIX2'] = diag/2 + 0.5

    pixscale = proj_plane_pixel_scales(orig_wcs)
    new_hdr['CD1_1'], new_hdr['CD1_2'] = -pixscale[0], 0.0
    new_hdr['CD2_1'], new_hdr['CD2_2'] =   0.0,        pixscale[1]
    new_wcs = WCS(new_hdr, naxis=2).celestial

    array, footprint = reproject_interp(
        (data, orig_wcs),
        new_wcs,
        shape_out=(diag, diag),
        order=0
    )

    if vmin is not None and vmax is not None:
        norm = ImageNormalize(vmin=vmin, vmax=vmax, stretch=LinearStretch())
    else:
        norm = ImageNormalize(array, interval=ZScaleInterval(), stretch=LinearStretch())

    fig = plt.figure(figsize=(10,8))
    ax  = fig.add_subplot(1,1,1, projection=new_wcs)

    im = ax.imshow(array, origin='lower', cmap='viridis', norm=norm)

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

    cbar = plt.colorbar(im,
                    ax=ax,
                    label='Flux',
                    shrink=0.9,
                    aspect=25,
                    pad=0.04)
    cbar.ax.tick_params(labelsize=number_size)
    cbar.ax.yaxis.label.set_size(label_size)

    output_filename = Path(filepath).stem + f'_slice{int(s)+1}.png'
    output_path = output_dir / output_filename
    plt.savefig(output_path)
    plt.close()
    return output_path


def convertToPNGWithAnnulus(
    theSlice: int,
    filepath: Path,
    rawdata: dict,
    center_sky: Optional[SkyCoord] = None,
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
    label_offset_px = 2

    with fits.open(filepath) as hdul:
        hdu      = hdul[1]
        data     = hdu.data[theSlice]
        orig_wcs = WCS(hdu.header, naxis=2).celestial

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

        array, footprint = reproject_interp(
            (data, orig_wcs), new_wcs, shape_out=(diag, diag), order=0
        )

    saved_paths: List[Path] = []

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

        if annulus is not None and xy_disp is not None:
            rin, rout = annulus
            x, y = xy_disp

            outer = Circle((x, y), rout, fill=False, linewidth=1.8,
                           edgecolor='white', alpha=0.95,
                           transform=ax.get_transform('pixel'), zorder=5)
            ax.add_patch(outer)
            inner = Circle((x, y), rin, fill=False, linewidth=1.2,
                           edgecolor='white', alpha=0.95, linestyle='--',
                           transform=ax.get_transform('pixel'), zorder=5)
            ax.add_patch(inner)

            if show_fill and rout > rin:
                fill = Circle((x, y), rout, fill=True, linewidth=0,
                              alpha=0.08, transform=ax.get_transform('pixel'), zorder=4)
                ax.add_patch(fill)
                hole = Circle((x, y), rin, fill=True, color='black', linewidth=0,
                              transform=ax.get_transform('pixel'), zorder=5)
                ax.add_patch(hole)

            if isLabel:
                text_kw = dict(
                    transform=ax.get_transform('pixel'),
                    ha='center', va='bottom',
                    fontsize=label_ring_size, color='white', zorder=6,
                    path_effects=[pe.Stroke(linewidth=2.5, foreground='black'), pe.Normal()],
                )
                ax.text(x, y + rin + label_offset_px, f"r_in = {rin}", **text_kw)
                ax.text(x, y + rout + label_offset_px, f"r_out = {rout}", **text_kw)

            suffix = f"_rin{int(round(rin))}_rout{int(round(rout))}_label" if isLabel else f"_rin{int(round(rin))}_rout{int(round(rout))}"
        else:
            suffix = ""

        out_name = f"{base_stem}{suffix}.png"
        out_path = out_dir / out_name
        plt.savefig(out_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        return out_path

    base_stem = f"{Path(filename).stem}_slice{s+1}"

    if not radii_pairs:
        saved_paths.append(render_and_save(output_dir, None, base_stem, annulus=None))
        return saved_paths

    saved_paths.append(render_and_save(output_dir, None, base_stem, annulus=None))
    for r_in_key, r_out_key in radii_pairs:
        frames_map = rawdata.get(r_in_key, {}).get(r_out_key, {}).get(filename, {})
        center_pix_orig = frames_map.get(str(s+1))
        if center_pix_orig is None:
            continue

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
    radii_pairs=None,
    n_grid=10,
    output_dir: Union[str, Path] = ".",
    vmin: float = None,
    vmax: float = None,
) -> List[Path]:
    """
    Export JWST FITS slice into a JSON file.
    If vmin/vmax are None, per-image ZScale is computed.
    Otherwise the provided vmin/vmax are used (set 2 / set 3).
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    s = theSlice
    filename = filepath.name
    base_stem = f"{Path(filename).stem}_slice{s+1}"

    center_pix_orig = None
    if radii_pairs:
        for r_in_key, r_out_key in radii_pairs:
            frames_map = rawdata.get(r_in_key, {}).get(r_out_key, {}).get(filename, {})
            center_pix_orig = frames_map.get(str(s+1))
            if center_pix_orig is not None:
                break

    output_filename = f"{base_stem}.json"
    output_path = output_dir / output_filename

    with fits.open(filepath) as hdul:
        hdu = hdul[1]
        data = hdu.data[s]
        orig_wcs = WCS(hdu.header, naxis=2).celestial

    ny, nx = data.shape
    diag = int(np.hypot(ny, nx))

    hdr = hdu.header.copy()
    hdr["NAXIS1"] = diag
    hdr["NAXIS2"] = diag
    hdr["CRPIX1"] = diag / 2 + 0.5
    hdr["CRPIX2"] = diag / 2 + 0.5

    pixscale = proj_plane_pixel_scales(orig_wcs)
    hdr["CD1_1"], hdr["CD1_2"] = -pixscale[0], 0.0
    hdr["CD2_1"], hdr["CD2_2"] = 0.0, pixscale[1]

    new_wcs = WCS(hdr, naxis=2).celestial

    array, footprint = reproject_interp(
        (data, orig_wcs),
        new_wcs,
        shape_out=(diag, diag),
        order=0
    )

    if vmin is None or vmax is None:
        interval = ZScaleInterval()
        vmin, vmax = interval.get_limits(array)

    xy_disp = None
    if center_pix_orig is not None:
        x0, y0 = float(center_pix_orig[0]), float(center_pix_orig[1])
        sky = orig_wcs.pixel_to_world(x0, y0)
        px, py = new_wcs.world_to_pixel(sky)
        xy_disp = (float(px), float(py))

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

    ra_grid = np.linspace(ra_min, ra_max, n_grid)
    dec_grid = np.linspace(dec_min, dec_max, n_grid)

    def sample_constant_ra(ra_deg):
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

    ra_lines = [
        {"ra_deg": float(r), "pixels": sample_constant_ra(r)}
        for r in ra_grid
    ]
    dec_lines = [
        {"dec_deg": float(d), "pixels": sample_constant_dec(d)}
        for d in dec_grid
    ]

    def tick_ra(r):
        world = SkyCoord(ra=r, dec=dec_min, unit="deg")
        px, py = new_wcs.world_to_pixel(world)
        label = SkyCoord(ra=r, dec=0, unit="deg").ra.to_string(unit="hour", sep=":", precision=1)
        return {"px": [float(px), float(py)], "label": label}

    def tick_dec(d):
        world = SkyCoord(ra=ra_min, dec=d, unit="deg")
        px, py = new_wcs.world_to_pixel(world)
        label = SkyCoord(ra=0, dec=d, unit="deg").dec.to_string(unit="deg", sep=":", precision=1)
        return {"px": [float(px), float(py)], "label": label}

    ticks = {
        "ra": [tick_ra(r) for r in ra_grid],
        "dec": [tick_dec(d) for d in dec_grid]
    }

    def sanitize(x):
        if isinstance(x, float) and (np.isnan(x) or np.isinf(x)):
            return None
        return x

    data_list = array.astype(np.float32).tolist()
    data_list = [[sanitize(v) for v in row] for row in data_list]

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

    with open(output_path, "w") as f:
        json.dump(result, f)

    return output_path


def process_data(collection_name):
    rawdata = {}

    print("Fetching data from MongoDB")

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
                                    fn = str(fn)
                                    fr = str(fr)
                                    xy = (float(x), float(y))

                                    if fn not in target:
                                        target[fn] = {}
                                    target[fn][fr] = xy

    return rawdata


def _worker_convert_Annulus(filename, frame_idx, output_dir, rawdata_subdict, radii_pairs, isLabel):
    try:
        import matplotlib
        matplotlib.use("Agg")
        out_path = convertToPNGWithAnnulus(
            theSlice=frame_idx,
            filepath=Path(filename),
            rawdata=rawdata_subdict,
            radii_pairs=radii_pairs,
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


def _worker_convert_normalImg(filename, frame_idx, output_dir, vmin, vmax):
    try:
        import matplotlib
        matplotlib.use("Agg")
        out_path = convertToPNG(
            theSlice=frame_idx,
            filepath=Path(filename),
            output_dir=Path(output_dir),
            vmin=vmin,
            vmax=vmax
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


def _worker_convert_imgJson(filename, frame_idx, output_dir, rawdata_subdict, radii_pairs, vmin, vmax):
    try:
        import matplotlib
        matplotlib.use("Agg")
        out_path = convertImgToJSON(
            theSlice=frame_idx,
            filepath=Path(filename),
            rawdata=rawdata_subdict,
            radii_pairs=radii_pairs,
            n_grid=10,
            output_dir=Path(output_dir),
            vmin=vmin,
            vmax=vmax
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
    path = Path(path)
    if path.suffix == ".gz":
        with gzip.open(path, "rt", encoding="utf-8") as f:
            return json.load(f)
    else:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)


def git_commit_push(target_dir: Path, message: str) -> bool:
    target_dir = Path(target_dir).resolve()

    p = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=str(target_dir),
        capture_output=True, text=True
    )
    if p.returncode != 0:
        raise RuntimeError(f"{target_dir} is not inside a Git repository.")
    repo_root = Path(p.stdout.strip())

    rel = os.path.relpath(str(target_dir), str(repo_root))
    subprocess.run(["git", "add", "-A", "--", rel], cwd=str(repo_root), check=True)

    diff = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=str(repo_root))
    if diff.returncode == 0:
        return False

    subprocess.run(["git", "commit", "-m", message], cwd=str(repo_root), check=True)
    subprocess.run(["git", "push", "-u", "origin", "HEAD"], cwd=str(repo_root), check=True)
    return True


def git_push_in_batches_with_progress(target_dir: Path, message: str,
                                      batch_size: int = 100,
                                      patterns=("*.png",),
                                      pack_threads: int | None = 0) -> int:
    target_dir = Path(target_dir).resolve()
    p = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                       cwd=str(target_dir), capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"{target_dir} is not inside a Git repository.")
    repo_root = Path(p.stdout.strip())
    rel = os.path.relpath(str(target_dir), str(repo_root))

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

        subprocess.run(["git", "reset", "-q", "HEAD", "--", rel], cwd=str(repo_root))
        subprocess.run(["git", "add", "--"] + batch, cwd=str(repo_root), check=True)

        if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=str(repo_root)).returncode != 0:
            subprocess.run(["git", "commit",
                            "-m", f"{message} (+{len(batch)} files, batch {batch_no})"],
                           cwd=str(repo_root), check=True)
            push_cmd = ["git"]
            if pack_threads is not None:
                push_cmd += ["-c", f"pack.threads={pack_threads}"]
            push_cmd += ["push", "origin", "HEAD"]
            subprocess.run(push_cmd, cwd=str(repo_root), check=True)

            pushed += len(batch)
            print(f"[git] {pushed}/{total} pushed (batch {batch_no}, +{len(batch)})")

    return pushed


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
    print("----------------------------------------------------------------------------------------------")
    print("\n")
    print("\n")
    print("\n")


def compute_global_norm(all_fileLists):
    """
    Load ALL frames across ALL files for a global vmin/vmax via ZScale.
    Returns (None, None) if no files could be read.
    """
    all_samples = []
    for filepath in all_fileLists:
        try:
            with fits.open(filepath, memmap=True) as hdul:
                data = hdul[1].data
                flat = data[np.isfinite(data)].ravel()
                all_samples.append(flat)
        except Exception as e:
            print(f"[norm] Skipping {filepath}: {e}")

    if not all_samples:
        return None, None
    combined = np.concatenate(all_samples)
    vmin, vmax = ZScaleInterval().get_limits(combined)
    return float(vmin), float(vmax)


def main():
    rawdata = load_json(r"/mnt/VIZ/work/proemsri/jwst/rawdata.json")
    log_path = Path("/mnt/VIZ/work/proemsri/jwst/errors.txt")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("file\tframe\terror\ttraceback_last_line\n")

    # -------------------------
    # 1. Collect all files grouped by (epoch, wave_type), plus SW/LW buckets
    # -------------------------
    epoch_wave_files = {}
    all_files = []
    sw_files_all = []
    lw_files_all = []

    for epoch in ["epoch1", "epoch2"]:
        for wave_type in ["lw", "sw"]:
            if epoch == "epoch1":
                sw_files = sorted(original_path.glob("jw01666001001*_nrcb1/*crfints.fits"))
                lw_files = sorted(original_path.glob("jw01666001001*_nrcblong/*crfints.fits"))
            else:
                sw_files = sorted(original_path.glob("jw01666003001*_nrcb1/*crfints.fits"))
                lw_files = sorted(original_path.glob("jw01666003001*_nrcblong/*crfints.fits"))

            fileList = lw_files if wave_type == "lw" else sw_files
            epoch_wave_files[(epoch, wave_type)] = fileList
            all_files.extend(fileList)
            if wave_type == "sw":
                sw_files_all.extend(fileList)
            else:
                lw_files_all.extend(fileList)

    # -------------------------
    # 2. Compute norms for set2 (global) and set3 (per-wave).
    #    Set1 uses per-image ZScale (vmin=vmax=None) -> nothing to precompute.
    # -------------------------
    print("Computing GLOBAL normalization (set 2) across all files...")
    vmin_global, vmax_global = compute_global_norm(all_files)
    print(f"  Global: vmin={vmin_global}, vmax={vmax_global}")

    print("Computing SW normalization (set 3)...")
    vmin_sw, vmax_sw = compute_global_norm(sw_files_all)
    print(f"  SW: vmin={vmin_sw}, vmax={vmax_sw}")

    print("Computing LW normalization (set 3)...")
    vmin_lw, vmax_lw = compute_global_norm(lw_files_all)
    print(f"  LW: vmin={vmin_lw}, vmax={vmax_lw}")

    # -------------------------
    # 3. Define the three sets
    # -------------------------
    sets_config = [
        {
            "name": "set1_original",
            "get_norm": lambda epoch, wave: (None, None),
        },
        {
            "name": "set2_global",
            "get_norm": lambda epoch, wave: (vmin_global, vmax_global),
        },
        {
            "name": "set3_by_wave",
            "get_norm": lambda epoch, wave: (vmin_sw, vmax_sw) if wave == "sw"
                                            else (vmin_lw, vmax_lw),
        },
    ]

    # Sidecar recording which scales were used (handy for reproducing later)
    norm_record = {
        "set1_original": "per-image ZScale",
        "set2_global": {"vmin": vmin_global, "vmax": vmax_global},
        "set3_by_wave": {
            "sw": {"vmin": vmin_sw, "vmax": vmax_sw},
            "lw": {"vmin": vmin_lw, "vmax": vmax_lw},
        },
    }
    (json_img_dir / "norm_record.json").write_text(json.dumps(norm_record, indent=2))

    # -------------------------
    # 4. Run each set
    # -------------------------
    max_workers = 256

    for cfg in sets_config:
        set_name = cfg["name"]
        get_norm = cfg["get_norm"]

        print(f"\n{'='*70}")
        print(f"Building tasks for {set_name}")
        print(f"{'='*70}")

        tasks_normalImg = []
        tasks_imgJson = []

        for epoch in ["epoch1", "epoch2"]:
            for wave_type in ["lw", "sw"]:
                fileList = epoch_wave_files[(epoch, wave_type)]
                vmin, vmax = get_norm(epoch, wave_type)

                radii_pairs = [
                    (r_in_key, r_out_key)
                    for r_in_key, r_outs in rawdata[epoch][wave_type].items()
                    for r_out_key in r_outs.keys()
                ]

                group_out_dir_png  = full_size_dir / set_name / epoch / wave_type
                group_out_dir_json = json_img_dir  / set_name / epoch / wave_type
                group_out_dir_png.mkdir(parents=True, exist_ok=True)
                group_out_dir_json.mkdir(parents=True, exist_ok=True)

                for filename in fileList:
                    try:
                        with fits.open(filename, memmap=True) as f:
                            data = f["SCI"].data
                            nframes = data.shape[0] if data.ndim == 3 else 1
                    except Exception as e:
                        with open(log_path, "a", encoding="utf-8") as logf:
                            logf.write(f"{filename}\t-1\tOpenError: {e}\n")
                        continue

                    for i in range(0, nframes):
                        tasks_normalImg.append((
                            str(filename), i, str(group_out_dir_png), vmin, vmax
                        ))
                        tasks_imgJson.append((
                            str(filename), i, str(group_out_dir_json),
                            rawdata[epoch][wave_type], radii_pairs, vmin, vmax
                        ))

        run_tasks(f"{set_name}-PNG",  tasks_normalImg, _worker_convert_normalImg, max_workers, log_path)
        run_tasks(f"{set_name}-JSON", tasks_imgJson,   _worker_convert_imgJson,   max_workers, log_path)

    print("\nAll three sets processed.")
    print("See error log at:", log_path)

    # -------------------------
    # 5. Push all JSON (all three sets live under json_img_dir)
    # -------------------------
    pushed = git_push_in_batches_with_progress(
        json_img_dir,
        message="Update image data JSON (3 scaling sets)",
        batch_size=500,
        patterns=("*.json",),
        pack_threads=0,
    )
    print(f"[git] pushed {pushed} files.")


if __name__ == "__main__":
    mp.freeze_support()
    main()