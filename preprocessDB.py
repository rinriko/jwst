# preprocessDB.py
from pymongo import MongoClient
from pathlib import Path
import re
import h5py
import copy
from astropy.time import Time
from astropy import units as u, constants as c
import numpy as np
import json
import config
import time


def get_db(database_name):
    client = MongoClient(config.MONGO_URI)
    db = client[database_name]
    return db

def close_db(client):
    client.close()

def convert_time_units(mjd_times, unit):
    """
    Convert a list of Modified Julian Date (MJD) times to the specified unit.

    Parameters:
    - mjd_times (list or np.array): List of MJD times.
    - unit (str): Unit to convert to. Supported units are 'second', 'minute', 'hour', 'day'.

    Returns:
    - converted_times (np.array): Array of times converted to the specified unit.
    """
    time = Time(mjd_times, format="mjd", scale="tdb")

    if unit == 'second':
        converted_times = (time.mjd - time.mjd.min()) * 86400.0  # seconds
    elif unit == 'minute':
        converted_times = (time.mjd - time.mjd.min()) * 1440.0  # minutes
    elif unit == 'hour':
        converted_times = (time.mjd - time.mjd.min()) * 24.0  # hours
    elif unit == 'day':
        converted_times = time.mjd - time.mjd.min()  # days
    else:
        raise ValueError(
            "Unsupported time unit. Supported units are 'second', 'minute', 'hour', 'day'.")

    return converted_times

# Function to modify and concatenate strings
def modify_and_concat(fits, frame_value):
    # Remove the .fits extension and add the slice and .png suffix
    modified_fits = fits.replace('.fits', f'_slice{frame_value}.png')
    return modified_fits

def pad_and_align_data(df_rawdata):
    for wave_type in df_rawdata:
        # Collect all unique time values
        all_times = set()
        for r_in in df_rawdata[wave_type]:
            for r_out in df_rawdata[wave_type][r_in]:
                all_times.update(
                    df_rawdata[wave_type][r_in][r_out]["time_mjd"])

        # Create a sorted list of all unique time values
        sorted_all_times = sorted(all_times)

        for r_in in df_rawdata[wave_type]:
            for r_out in df_rawdata[wave_type][r_in]:
                data = df_rawdata[wave_type][r_in][r_out]

                # Create a map of time to index
                time_to_index = {time: i for i,
                                    time in enumerate(data["time_mjd"])}

                def align_list(lst, time_list, default_value=None):
                    aligned_list = [default_value] * len(sorted_all_times)
                    for i, time in enumerate(time_list):
                        if time in time_to_index:
                            aligned_list[sorted_all_times.index(time)] = lst[i] if i < len(lst) else default_value
                    return aligned_list

                # Align each list according to sorted_all_times
                aligned_data = {key: align_list(
                    data[key], data["time_mjd"]) for key in data}
                aligned_data["time_mjd"] = sorted_all_times

                # Update the data with aligned lists
                df_rawdata[wave_type][r_in][r_out] = aligned_data

    return df_rawdata

def process_data(collection_name):
    rawdata = {}
    df_rawdata = {}
    dataList = []

    print("Fetching data from MongoDB")
    # db = get_db("jwst")
    
    client = MongoClient(config.MONGO_LOCAL_URI)
    db = client["jwst"]

    collection = db[collection_name]
    epochs = collection.distinct('epoch')

    for epoch in epochs:
        if epoch not in rawdata:
            rawdata[epoch] = {}
            df_rawdata[epoch] = {}

        types = collection.distinct('type', {'epoch': epoch})
        for wave_type in types:
            if wave_type not in rawdata[epoch]:
                rawdata[epoch][wave_type] = {}
                df_rawdata[epoch][wave_type] = {}
            r_in_values = collection.distinct(
                'r_in', {'epoch': epoch, 'type': wave_type})
            for r_in in r_in_values:
                if r_in not in rawdata[epoch][wave_type]:
                    rawdata[epoch][wave_type][r_in] = {}
                if r_in not in df_rawdata[epoch][wave_type]:
                    df_rawdata[epoch][wave_type][r_in] = {}
                r_out_values = collection.distinct(
                    'r_out', {'epoch': epoch, 'type': wave_type, 'r_in': r_in})
                for r_out in r_out_values:
                    if r_out not in rawdata[epoch][wave_type][r_in]:
                        rawdata[epoch][wave_type][r_in][r_out] = {}
                    if r_out not in df_rawdata[epoch][wave_type][r_in]:
                        df_rawdata[epoch][wave_type][r_in][r_out] = {}
                    if f"{epoch}_{r_in}_{r_out}" not in dataList:
                        dataList.append(f"{epoch}_{r_in}_{r_out}")
                    cursor = collection.find(
                        {'epoch': epoch, 'type': wave_type, 'r_in': r_in, 'r_out': r_out})
                    for doc in cursor:
                        if 'computed_psf' in doc:
                            if f"{epoch}_{r_in}_{r_out}" not in dataList:
                                dataList.append(f"{epoch}_{r_in}_{r_out}")

                            phase_values_sorted = np.array(
                                doc['computed_psf']['phase_values_sorted'])
                            time_sorted = np.array(
                                doc['computed_psf']['time_sorted'])
                            psf_flux_sorted = np.array(
                                doc['computed_psf']['psf_flux_sorted'])
                            psf_flux_unc_sorted = np.array(
                                doc['computed_psf']['psf_flux_unc_sorted'])
                            fits_file_name_sorted = np.array(
                                doc['computed_psf']['fits_file_name_sorted'])
                            frame_sorted = np.array(
                                doc['computed_psf']['frame_sorted'])
                            concatenated_array_sorted = np.array([modify_and_concat(fits, frm) for fits, frm in zip(fits_file_name_sorted, frame_sorted)])
                            customdata_sorted = np.array(
                                doc['computed_psf']['customdata_phase'])

                            # customdata_sorted_objects = [
                            #     {**json.loads(item), "time": Time(json.loads(item)[
                            #         "mjd"], format="mjd", scale="tdb").datetime.strftime('%Y-%m-%d %H:%M:%S.%f')[:-5]}
                            #     for item in customdata_sorted
                            # ]
                            # Process customdata and add the concatenated filenames
                            customdata_sorted_objects = [
                                {**json.loads(item), 
                                "time": Time(json.loads(item)["mjd"], format="mjd", scale="tdb").datetime.strftime('%Y-%m-%d %H:%M:%S.%f')[:-5],
                                "filename": epoch+"/"+wave_type+"/"+concatenated_array_sorted[i],
                                'epoch': epoch, 'type': wave_type, 'r_in': r_in, 'r_out': r_out} 
                                for i, item in enumerate(customdata_sorted)
                            ]

                            # time = Time(
                            #     np.array(doc['computed_psf']['time']), format="mjd", scale="tdb")
                            time = np.array(
                                doc['computed_psf']['time'])
                            time_mjd = np.array(
                                doc['computed_psf']['time'])
                            time_second = np.array(
                                doc['computed_psf']['time_second'])
                            time_minute = np.array(
                                doc['computed_psf']['time_minute'])
                            time_hour = np.array(
                                doc['computed_psf']['time_hour'])
                            time_day = np.array(
                                doc['computed_psf']['time_day'])
                            phase_values = np.array(
                                doc['computed_psf']['phase_values'])
                            psf_flux_time = np.array(
                                doc['computed_psf']['psf_flux_time'])
                            psf_flux_unc_time = np.array(
                                doc['computed_psf']['psf_flux_unc_time'])
                            fits_file_name = np.array(
                                doc['computed_psf']['fits_file_name'])
                            frame = np.array(doc['computed_psf']['frame'])
                            concatenated_array = np.array([modify_and_concat(fits, frm) for fits, frm in zip(fits_file_name, frame)])
                            customdata_time = np.array(
                                doc['computed_psf']['customdata_time'])

                            # customdata_time_objects = [
                            #     {**json.loads(item), "time": Time(json.loads(item)[
                            #         "mjd"], format="mjd", scale="tdb").datetime.strftime('%Y-%m-%d %H:%M:%S.%f')[:-5]}
                            #     for item in customdata_time
                            # ]
                            # Process customdata and add the concatenated filenames
                            customdata_time_objects = [
                                {**json.loads(item), 
                                "time": Time(json.loads(item)["mjd"], format="mjd", scale="tdb").datetime.strftime('%Y-%m-%d %H:%M:%S.%f')[:-5],
                                "filename": epoch+"/"+wave_type+"/"+concatenated_array[i],'epoch': epoch, 'type': wave_type, 'r_in': r_in, 'r_out': r_out} 
                                for i, item in enumerate(customdata_time)
                            ]

                            phase_values_phase = np.concatenate(
                                (phase_values_sorted, phase_values_sorted + 1))
                            time_mjd_phase = np.concatenate(
                                (time_sorted, time_sorted))
                            psf_flux_phase = np.concatenate(
                                (psf_flux_sorted, psf_flux_sorted))
                            psf_flux_unc_phase = np.concatenate(
                                (psf_flux_unc_sorted, psf_flux_unc_sorted))
                            frame_phase = np.concatenate(
                                (frame_sorted, frame_sorted))
                            customdata_phase = np.concatenate(
                                (customdata_sorted_objects, customdata_sorted_objects))

                            df_rawdata[epoch][wave_type][r_in][r_out] = {
                                "time_mjd": time_mjd,
                                "psf_flux_time": psf_flux_time,
                                "psf_flux_unc_time": psf_flux_unc_time,
                            }

                            valid_mask_time = ~np.isnan(psf_flux_time)
                            valid_mask_phase = ~np.isnan(psf_flux_phase)


                            rawdata[epoch][wave_type][r_in][r_out] = {
                                "time": list(np.array(time)[valid_mask_time]),
                                "time_mjd": list(np.array(time)[valid_mask_time]),
                                "time_second": list(np.array(time_second)[valid_mask_time]),
                                "time_minute": list(np.array(time_minute)[valid_mask_time]),
                                "time_hour": list(np.array(time_hour)[valid_mask_time]),
                                "time_day": list(np.array(time_day)[valid_mask_time]),
                                "phase_values": list(np.array(phase_values)[valid_mask_time]),
                                "psf_flux_time": list(np.array(psf_flux_time)[valid_mask_time]),
                                "psf_flux_unc_time": list(np.array(psf_flux_unc_time)[valid_mask_time]),
                                "frame": list(np.array(frame)[valid_mask_time].astype(str)),
                                "customdata_time": list(np.array(customdata_time_objects)[valid_mask_time]),

                                "phase_values_phase": list(np.array(phase_values_phase)[valid_mask_phase]),
                                "time_mjd_phase": list(np.array(time_mjd_phase)[valid_mask_phase]),
                                "psf_flux_phase": list(np.array(psf_flux_phase)[valid_mask_phase]),
                                "psf_flux_unc_phase": list(np.array(psf_flux_unc_phase)[valid_mask_phase]),
                                "frame_phase": list(np.array(frame_phase)[valid_mask_phase].astype(str)),
                                "customdata_phase": list(np.array(customdata_phase)[valid_mask_phase]),
                            }
    data_for_df = {}
    for epoch in df_rawdata:
        data_for_df[epoch] = pad_and_align_data(df_rawdata[epoch])
        print("Data fetching complete", epoch)
    return rawdata, dataList, data_for_df


def write_to_db(rawdata, dataList, data_for_df, collection_name):
    print("Start writing")
    # Insert rawdata into MongoDB
    print("jwst_rawdata")
    db = get_db("jwst_rawdata")
    collection = db[collection_name]
    for epoch in rawdata:
        for wave_type in rawdata[epoch]:
            for r_in in rawdata[epoch][wave_type]:
                for r_out in rawdata[epoch][wave_type][r_in]:
                    doc = rawdata[epoch][wave_type][r_in][r_out]
                    doc['_id'] = f"{epoch}_{wave_type}_{r_in}_{r_out}"
                    doc['epoch'] = epoch
                    doc['wave_type'] = wave_type
                    doc['r_in'] = r_in
                    doc['r_out'] = r_out
                    collection.insert_one(doc)
    close_db(db.client)

    # Insert dataList into MongoDB
    print("jwst_dataList")
    db = get_db("jwst_dataList")
    collection_dataList = db[collection_name]
    for item in dataList:
        collection_dataList.insert_one({"item": item})
    close_db(db.client)

    # Insert data_for_df into MongoDB
    print("df")
    db = get_db("df")
    collection_data_for_df = db[collection_name]
    for epoch in data_for_df:
        for wave_type in data_for_df[epoch]:
            for r_in in data_for_df[epoch][wave_type]:
                for r_out in data_for_df[epoch][wave_type][r_in]:
                    doc = data_for_df[epoch][wave_type][r_in][r_out]
                    doc['_id'] = f"{epoch}_{wave_type}_{r_in}_{r_out}"
                    doc['epoch'] = epoch
                    doc['wave_type'] = wave_type
                    doc['r_in'] = r_in
                    doc['r_out'] = r_out
                    collection_data_for_df.insert_one(doc)
    close_db(db.client)
    print("Finished writing")

def write_to_json(rawdata, dataList, data_for_df, prefix=''):
    with open('rawdata.json', 'w') as f:
        json.dump(rawdata, f, indent=4)
    with open('dataList.json', 'w') as f:
        json.dump(dataList, f, indent=4)
    with open('data_for_df.json', 'w') as f:
        json.dump(data_for_df, f, indent=4)


def write_to_json_by_folder(rawdata, dataList, data_for_df, prefix='output'):
    base = Path(prefix)
    base.mkdir(parents=True, exist_ok=True)

    # 1) dataList
    (base / 'dataList.json').write_text(
        json.dumps(dataList, indent=2), encoding='utf-8'
    )

    # 2) rawdata split
    for epoch, epoch_dict in rawdata.items():
        for wave_type, type_dict in epoch_dict.items():
            for r_in, rin_dict in type_dict.items():
                for r_out, rout_data in rin_dict.items():
                    # ensure rout_data is JSON serializable
                    for k, v in rout_data.items():
                        if isinstance(v, np.ndarray):
                            rout_data[k] = v.tolist()
                    dest = base / 'rawdata' / str(epoch) / wave_type / str(r_in)
                    dest.mkdir(parents=True, exist_ok=True)
                    with (dest / f"{r_out}.json").open('w', encoding='utf-8') as f:
                        json.dump(rout_data, f, indent=2)

    # 3) df split (very similar)
    for epoch, epoch_dict in data_for_df.items():
        for wave_type, type_dict in epoch_dict.items():
            for r_in, rin_dict in type_dict.items():
                for r_out, rout_data in rin_dict.items():
                    # convert numpy arrays if any
                    for k, v in rout_data.items():
                        if isinstance(v, np.ndarray):
                            rout_data[k] = v.tolist()
                    dest = base / 'df' / str(epoch) / wave_type / str(r_in)
                    dest.mkdir(parents=True, exist_ok=True)
                    with (dest / f"{r_out}.json").open('w', encoding='utf-8') as f:
                        json.dump(rout_data, f, indent=2)

    print(f"✓ All done!  Files under “{prefix}/”")



rawdata, dataList, data_for_df = process_data('ZTF_J1539')

# write_to_db(rawdata, dataList, data_for_df, 'ZTF_J1539')
write_to_json(rawdata, dataList, data_for_df, 'ZTF_J1539')
write_to_json_by_folder(rawdata, dataList, data_for_df, 'ZTF_J1539')
