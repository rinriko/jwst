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

# Directory where your HDF5 files live
HDF5_DIR = Path(r"T:\JWST-Timing\jwst-idvl\jwst-data-raw-photon-count\hdf5")
HDF5_PATTERN = "Shaw_ZTF_J1539_photometry.{epoch}.{wave_type}.{r_in}.{r_out}.hdf5"


def convert_time_units(mjd_times, unit):
    """
    Convert a list of Modified Julian Date (MJD) times to the specified unit.
    """
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
        raise ValueError(
            "Unsupported time unit. Supported units are 'second', 'minute', 'hour', 'day'.")


def modify_and_concat(fits, frame_value):
    """Remove the .fits extension and add the slice and .png suffix."""
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
    """
    Scan hdf5_dir for files matching the naming pattern and return a list of
    (epoch, wave_type, r_in, r_out, filepath) tuples.
    """
    pattern = re.compile(
        r"Shaw_ZTF_J1539_photometry\."
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
                m.group("epoch"),
                m.group("wave_type"),
                m.group("r_in"),
                m.group("r_out"),
                f,
            ))
    return found


def process_data_from_hdf5(hdf5_dir=HDF5_DIR):
    rawdata = {}
    df_rawdata = {}
    dataList = []

    files = discover_hdf5_files(hdf5_dir)
    if not files:
        raise FileNotFoundError(f"No matching HDF5 files found in {hdf5_dir}")

    print(f"Found {len(files)} HDF5 file(s). Processing...")

    for epoch, wave_type, r_in, r_out, filepath in files:
        print(f"  Reading: {filepath.name}")
        if epoch != "epoch1":
            print(f"    Skipping {filepath.name} (not epoch1)")
            continue

        # Read the computed_psf table from HDF5
        try:
            computed_psf_table = Table.read(str(filepath), path="computed_psf")
        except Exception as e:
            print(f"    WARNING: could not read computed_psf from {filepath.name}: {e}")
            continue

        # ── pull columns (mirror what MongoDB stored) ──────────────────────
        col = lambda name: np.array(computed_psf_table[name])

        phase_values_sorted   = col('phase_values_sorted')
        time_sorted           = col('time_sorted')
        psf_flux_sorted       = col('psf_flux_sorted')
        psf_flux_unc_sorted   = col('psf_flux_unc_sorted')
        fits_file_name_sorted = col('fits_file_name_sorted').astype(str)
        frame_sorted          = col('frame_sorted')
        raw_photon_count        = col('raw_photon_count')
        raw_photon_count_err    = col('raw_photon_count_err')
        raw_photon_count_sorted = col('raw_photon_count_sorted')
        raw_photon_count_unc_sorted = col('raw_photon_count_unc_sorted')

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

        # ── customdata ─────────────────────────────────────────────────────
        # Support both a stored JSON string column and a plain MJD column.
        def build_customdata(mjd_arr, concat_arr, label):
            result = []
            for i, mjd in enumerate(mjd_arr):
                dt_str = Time(float(mjd), format="mjd", scale="tdb")\
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

        # If the table already stores JSON customdata strings, parse them;
        # otherwise build from MJD columns.
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

        # ── masks ──────────────────────────────────────────────────────────
        valid_mask_time  = ~np.isnan(psf_flux_time)
        valid_mask_phase = ~np.isnan(psf_flux_sorted)

        # ── populate nested dicts ──────────────────────────────────────────
        for d in (rawdata, df_rawdata):
            d.setdefault(epoch, {}) \
             .setdefault(wave_type, {}) \
             .setdefault(r_in, {})

        key = f"{epoch}_{r_in}_{r_out}"
        if key not in dataList:
            dataList.append(key)

        df_rawdata[epoch][wave_type][r_in][r_out] = {
            "time_mjd":           list(time_mjd),
            "psf_flux_time":      list(psf_flux_time),
            "psf_flux_unc_time":  list(psf_flux_unc_time),
            "customdata_time":    list(customdata_time_objects),
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
            "raw_photon_count":              list(raw_photon_count[valid_mask_time]),       # NEW
            "raw_photon_count_err":          list(raw_photon_count_err[valid_mask_time]),
            "frame":              list(frame[valid_mask_time].astype(str)),
            "customdata_time":    list(customdata_time_objects[valid_mask_time]),
            # phase-folded [0-1]
            "phase_values_phase": list(phase_values_sorted[valid_mask_phase]),
            "time_mjd_phase":     list(time_sorted[valid_mask_phase]),
            "psf_flux_phase":     list(psf_flux_sorted[valid_mask_phase]),
            "psf_flux_unc_phase": list(psf_flux_unc_sorted[valid_mask_phase]),
            "raw_photon_count_phase":        list(raw_photon_count_sorted[valid_mask_phase]),      # NEW
            "raw_photon_count_unc_phase":    list(raw_photon_count_unc_sorted[valid_mask_phase]),  # NEW
            "frame_phase":        list(frame_sorted[valid_mask_phase].astype(str)),
            "customdata_phase":   list(customdata_sorted_objects[valid_mask_phase]),
        }

    data_for_df = {}
    for epoch in df_rawdata:
        data_for_df[epoch] = pad_and_align_data(df_rawdata[epoch])
        print(f"Data processing complete for epoch: {epoch}")

    return rawdata, dataList, data_for_df


# ── output helpers (unchanged from original) ───────────────────────────────────

class NumpyEncoder(json.JSONEncoder):
    """Converts numpy scalars/arrays to native Python types for JSON serialization."""
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


def write_to_json(rawdata, dataList, data_for_df, prefix='T:\JWST-Timing\jwst-idvl\jwst-data-raw-photon-count'):
    with open('rawdata.json', 'w') as f:
        json.dump(rawdata, f, indent=4, cls=NumpyEncoder)
    with open('dataList.json', 'w') as f:
        json.dump(dataList, f, indent=4, cls=NumpyEncoder)
    with open('data_for_df.json', 'w') as f:
        json.dump(data_for_df, f, indent=4, cls=NumpyEncoder)


def write_to_json_by_folder(rawdata, dataList, data_for_df, prefix='T:\JWST-Timing\jwst-idvl\jwst-data-raw-photon-count\json'):
    base = Path(prefix)
    base.mkdir(parents=True, exist_ok=True)

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

    print(f'✓ All done!  Files under "{prefix}/"')


# ── entry point ────────────────────────────────────────────────────────────────

rawdata, dataList, data_for_df = process_data_from_hdf5(HDF5_DIR)

write_to_json(rawdata, dataList, data_for_df, 'ZTF_J1539')
write_to_json_by_folder(rawdata, dataList, data_for_df, 'ZTF_J1539')