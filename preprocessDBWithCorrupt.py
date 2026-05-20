# preprocessDB.py
from pathlib import Path
import re
import h5py
import copy
from astropy.time import Time
from astropy.table import Table
from astropy import units as u, constants as c
import numpy as np
import json
import time

# HDF5_DIR = Path(r"T:\JWST-Timing\jwst\output_with_Corrupt_Origin")
# HDF5_DIR = Path(r"T:\JWST-Timing\jwst\output_with_Corrupt_Recalculated")
# HDF5_DIR = Path(r"T:\JWST-Timing\jwst\output_with_Corrupt_Recalculated30")
# HDF5_DIR = Path(r"T:\JWST-Timing\jwst\output_with_Corrupt_Original30")
# HDF5_DIR = Path(r"T:\JWST-Timing\jwst\output_with_AfterJay_Original30")
# HDF5_DIR = Path(r"T:\JWST-Timing\jwst\output_with_AfterJay_Recalculated30")
# HDF5_DIR = Path(r"T:\JWST-Timing\jwst\output_with_FIT_Recalculated")
HDF5_DIR = Path(r"T:\JWST-Timing\jwst\output_with_FIT_original")

def convert_time_units(mjd_times, unit):
    t = Time(mjd_times, format="mjd", scale="tdb")
    if unit == 'second':
        return (t.mjd - t.mjd.min()) * 86400.0
    elif unit == 'minute':
        return (t.mjd - t.mjd.min()) * 1440.0
    elif unit == 'hour':
        return (t.mjd - t.mjd.min()) * 24.0
    elif unit == 'day':
        return t.mjd - t.mjd.min()
    else:
        raise ValueError("Unsupported time unit.")


def modify_and_concat(fits, frame_value):
    return fits.replace('.fits', f'_slice{frame_value}.png')


def pad_and_align_data(df_rawdata):
    for wave_type in df_rawdata:
        all_times = set()
        for r_in in df_rawdata[wave_type]:
            for r_out in df_rawdata[wave_type][r_in]:
                all_times.update(df_rawdata[wave_type][r_in][r_out]["time_mjd"])

        sorted_all_times = sorted(all_times)

        for r_in in df_rawdata[wave_type]:
            for r_out in df_rawdata[wave_type][r_in]:
                data = df_rawdata[wave_type][r_in][r_out]
                time_to_index = {t: i for i, t in enumerate(data["time_mjd"])}

                def align_list(lst, time_list, default_value=None):
                    aligned = [default_value] * len(sorted_all_times)
                    for i, t in enumerate(time_list):
                        if t in time_to_index:
                            aligned[sorted_all_times.index(t)] = lst[i] if i < len(lst) else default_value
                    return aligned

                aligned_data = {key: align_list(data[key], data["time_mjd"]) for key in data}
                aligned_data["time_mjd"] = sorted_all_times
                df_rawdata[wave_type][r_in][r_out] = aligned_data

    return df_rawdata


def discover_hdf5_files(hdf5_dir):
    pattern = re.compile(
        r"Shaw_ZTF_J1539_photometry\."
        r"(?P<excl_label>[^.]+)\."
        r"(?P<epoch>[^.]+)\."
        r"(?P<wave_type>[^.]+)\."
        r"(?P<r_in>[^.]+)\."
        r"(?P<r_out>[^.]+)\.hdf5$"
    )
    found = []
    for f in Path(hdf5_dir).glob("Shaw_ZTF_J1539_photometry.*.hdf5"):
        m = pattern.match(f.name)
        if m:
            found.append((
                m.group("excl_label"),
                m.group("epoch"),
                m.group("wave_type"),
                m.group("r_in"),
                m.group("r_out"),
                f,
            ))
    return found


def process_data_from_hdf5(hdf5_dir=HDF5_DIR):
    # excl_label → { rawdata, df_rawdata, dataList }
    results_by_excl = {}

    files = discover_hdf5_files(hdf5_dir)
    if not files:
        raise FileNotFoundError(f"No matching HDF5 files found in {hdf5_dir}")

    print(f"Found {len(files)} HDF5 file(s). Processing...")

    for excl_label, epoch, wave_type, r_in, r_out, filepath in files:
        print(f"  Reading: {filepath.name}")
        if epoch != "epoch1":
            print(f"    Skipping {filepath.name} (not epoch1)")
            continue

        # init bucket for this excl_label
        if excl_label not in results_by_excl:
            results_by_excl[excl_label] = {
                "rawdata": {},
                "df_rawdata": {},
                "dataList": [],
            }

        bucket = results_by_excl[excl_label]
        rawdata    = bucket["rawdata"]
        df_rawdata = bucket["df_rawdata"]
        dataList   = bucket["dataList"]

        try:
            computed_psf_table = Table.read(str(filepath), path="computed_psf")
        except Exception as e:
            print(f"    WARNING: could not read computed_psf from {filepath.name}: {e}")
            continue

        col = lambda name: np.array(computed_psf_table[name])

        phase_values_sorted   = col('phase_values_sorted')
        time_sorted           = col('time_sorted')
        psf_flux_sorted       = col('psf_flux_sorted')
        psf_flux_unc_sorted   = col('psf_flux_unc_sorted')
        fits_file_name_sorted = col('fits_file_name_sorted').astype(str)
        frame_sorted          = col('frame_sorted')

        time_mjd          = col('time')
        time_second       = col('time_second')
        time_minute       = col('time_minute')
        time_hour         = col('time_hour')
        time_day          = col('time_day')
        phase_values      = col('phase_values')
        psf_flux_time     = col('psf_flux_time')
        psf_flux_unc_time = col('psf_flux_unc_time')
        fits_file_name    = col('fits_file_name').astype(str)
        frame             = col('frame')

        def build_customdata(mjd_arr, concat_arr, label):
            result = []
            for i, mjd in enumerate(mjd_arr):
                dt_str = Time(float(mjd), format="mjd", scale="tdb") \
                             .datetime.strftime('%Y-%m-%d %H:%M:%S.%f')[:-5]
                result.append({
                    "mjd": float(mjd),
                    "time": dt_str,
                    "filename": f"{epoch}/{wave_type}/{concat_arr[i]}",
                    "epoch": epoch,
                    "type": wave_type,
                    "r_in": r_in,
                    "r_out": r_out,
                })
            return np.array(result, dtype=object)

        concat_sorted = np.array([
            modify_and_concat(f, fr)
            for f, fr in zip(fits_file_name_sorted, frame_sorted)
        ])
        concat_time = np.array([
            modify_and_concat(f, fr)
            for f, fr in zip(fits_file_name, frame)
        ])

        if 'customdata_phase' in computed_psf_table.colnames:
            raw_cp = col('customdata_phase').astype(str)
            customdata_sorted_objects = np.array([
                {**json.loads(item),
                 "time": Time(json.loads(item)["mjd"], format="mjd", scale="tdb")
                             .datetime.strftime('%Y-%m-%d %H:%M:%S.%f')[:-5],
                 "filename": f"{epoch}/{wave_type}/{concat_sorted[i]}",
                 "epoch": epoch, "type": wave_type, "r_in": r_in, "r_out": r_out}
                for i, item in enumerate(raw_cp)
            ], dtype=object)
        else:
            customdata_sorted_objects = build_customdata(time_sorted, concat_sorted, "phase")

        if 'customdata_time' in computed_psf_table.colnames:
            raw_ct = col('customdata_time').astype(str)
            customdata_time_objects = np.array([
                {**json.loads(item),
                 "time": Time(json.loads(item)["mjd"], format="mjd", scale="tdb")
                             .datetime.strftime('%Y-%m-%d %H:%M:%S.%f')[:-5],
                 "filename": f"{epoch}/{wave_type}/{concat_time[i]}",
                 "epoch": epoch, "type": wave_type, "r_in": r_in, "r_out": r_out}
                for i, item in enumerate(raw_ct)
            ], dtype=object)
        else:
            customdata_time_objects = build_customdata(time_mjd, concat_time, "time")

        valid_mask_time  = ~np.isnan(psf_flux_time)
        valid_mask_phase = ~np.isnan(psf_flux_sorted)

        for d in (rawdata, df_rawdata):
            d.setdefault(epoch, {}) \
             .setdefault(wave_type, {}) \
             .setdefault(r_in, {})

        key = f"{epoch}_{r_in}_{r_out}"
        if key not in dataList:
            dataList.append(key)

        df_rawdata[epoch][wave_type][r_in][r_out] = {
            "time_mjd":          list(time_mjd),
            "psf_flux_time":     list(psf_flux_time),
            "psf_flux_unc_time": list(psf_flux_unc_time),
            "customdata_time":   list(customdata_time_objects),
        }

        rawdata[epoch][wave_type][r_in][r_out] = {
            "time":               list(time_mjd[valid_mask_time]),
            "time_mjd":           list(time_mjd[valid_mask_time]),
            "time_second":        list(time_second[valid_mask_time]),
            "time_minute":        list(time_minute[valid_mask_time]),
            "time_hour":          list(time_hour[valid_mask_time]),
            "time_day":           list(time_day[valid_mask_time]),
            "phase_values":       list(phase_values[valid_mask_time]),
            "psf_flux_time":      list(psf_flux_time[valid_mask_time]),
            "psf_flux_unc_time":  list(psf_flux_unc_time[valid_mask_time]),
            "frame":              list(frame[valid_mask_time].astype(str)),
            "customdata_time":    list(customdata_time_objects[valid_mask_time]),
            "phase_values_phase": list(phase_values_sorted[valid_mask_phase]),
            "time_mjd_phase":     list(time_sorted[valid_mask_phase]),
            "psf_flux_phase":     list(psf_flux_sorted[valid_mask_phase]),
            "psf_flux_unc_phase": list(psf_flux_unc_sorted[valid_mask_phase]),
            "frame_phase":        list(frame_sorted[valid_mask_phase].astype(str)),
            "customdata_phase":   list(customdata_sorted_objects[valid_mask_phase]),
        }

    # finalize df per excl_label
    final = {}
    for excl_label, bucket in results_by_excl.items():
        data_for_df = {}
        for ep in bucket["df_rawdata"]:
            data_for_df[ep] = pad_and_align_data(bucket["df_rawdata"][ep])
            print(f"  [{excl_label}] Data processing complete for epoch: {ep}")
        final[excl_label] = {
            "rawdata":     bucket["rawdata"],
            "dataList":    bucket["dataList"],
            "data_for_df": data_for_df,
        }

    return final


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


def write_to_json_by_folder(final, base_prefix='ZTF_J1539_WITH_FIT_ORIGINAL'):
    for excl_label, bucket in final.items():
        # e.g. ZTF_J1539_WITH_CORRUPT_ORIGIN
        prefix = f"{base_prefix}_{excl_label}"
        base = Path(prefix)
        base.mkdir(parents=True, exist_ok=True)

        rawdata    = bucket["rawdata"]
        dataList   = bucket["dataList"]
        data_for_df = bucket["data_for_df"]

        (base / 'dataList.json').write_text(
            json.dumps(dataList, indent=2, cls=NumpyEncoder), encoding='utf-8'
        )

        for epoch, epoch_dict in rawdata.items():
            for wave_type, type_dict in epoch_dict.items():
                for r_in, rin_dict in type_dict.items():
                    for r_out, rout_data in rin_dict.items():
                        for k, v in rout_data.items():
                            if isinstance(v, np.ndarray):
                                rout_data[k] = v.tolist()
                        dest = base / 'rawdata' / str(epoch) / wave_type / str(r_in)
                        dest.mkdir(parents=True, exist_ok=True)
                        with (dest / f"{r_out}.json").open('w', encoding='utf-8') as f:
                            json.dump(rout_data, f, indent=2, cls=NumpyEncoder)

        for epoch, epoch_dict in data_for_df.items():
            for wave_type, type_dict in epoch_dict.items():
                for r_in, rin_dict in type_dict.items():
                    for r_out, rout_data in rin_dict.items():
                        for k, v in rout_data.items():
                            if isinstance(v, np.ndarray):
                                rout_data[k] = v.tolist()
                        dest = base / 'df' / str(epoch) / wave_type / str(r_in)
                        dest.mkdir(parents=True, exist_ok=True)
                        with (dest / f"{r_out}.json").open('w', encoding='utf-8') as f:
                            json.dump(rout_data, f, indent=2, cls=NumpyEncoder)

        print(f'✓ Done: {prefix}/')


# ── entry point ────────────────────────────────────────────────────────────────

final = process_data_from_hdf5(HDF5_DIR)
write_to_json_by_folder(final, base_prefix='ZTF_J1539_WITH_FIT_ORIGINAL')