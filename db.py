# db.py
from pymongo import MongoClient
from pathlib import Path
import re
import copy
from astropy.time import Time
from astropy import units as u, constants as c
import numpy as np
import json
import config
import time

current_directory = Path.cwd()

def get_db(database_name):
    client = MongoClient(config.MONGO_URI)
    db = client[database_name]
    return db

def close_db(client):
    client.close()

def get_data(db_name, rawdata, data_for_df, collection_name, isDB, epoch, wave_type, r_in, r_out):
    id = f"{epoch}_{wave_type.lower()}_{r_in}_{r_out}"
    if db_name == "jwst_rawdata":
        if isDB:
            if id not in rawdata:
                db = get_db(db_name)
                collection = db[collection_name]
                rawdata[id] = collection.find_one({'_id': id})
                close_db(db.client)
            return rawdata[id]
        else:
            return rawdata[epoch][wave_type.lower()][str(r_in)][str(r_out)]
    elif db_name == "df":
        if isDB:
            if id not in data_for_df:
                db = get_db(db_name)
                collection = db[collection_name]
                data_for_df[id] = collection.find_one({'_id': id})
                close_db(db.client)
            return data_for_df[id]
        else:
            return data_for_df[epoch][wave_type.lower()][str(r_in)][str(r_out)]
        

def fetching_data(collection_name, isDB):
    rawdata = {}
    data_for_df = {}
    dataList = []
    if isDB:
        print("Fetching data from MongoDB")
        # print("jwst_rawdata")
        # db = get_db("jwst_rawdata")
        # collection = db[collection_name]
        # cursor = collection.find({})
        # for document in cursor:
        #     rawdata[document['_id']] = document
        # close_db(db.client)

        print("jwst_dataList")
        db = get_db("jwst_dataList")
        collection = db[collection_name]
        cursor = collection.find({})
        for document in cursor:
            dataList.append({'label': document['item'], 'value': document['item']})
        close_db(db.client)

        # print("df")
        # db = get_db("df")
        # collection = db[collection_name]
        # cursor = collection.find({})
        # for document in cursor:
        #     data_for_df[document['_id']] = document
        # close_db(db.client)

        print("Data fetching complete")
        # return rawdata, dataList, data_for_df
        return rawdata, dataList, data_for_df
    elif not isDB:
        print("Fetching data from JSON file")
        with open('./static/data/rawdata.json', 'r') as f:
            rawdata = json.load(f)
        with open('./static/data/dataList.json', 'r') as f:
            cursor = json.load(f)
            for document in cursor:
                dataList.append({'label': document, 'value': document})
        with open('./static/data/data_for_df.json', 'r') as f:
            data_for_df = json.load(f)
        print("Data fetching complete")
        return rawdata, dataList, data_for_df
    #     print("Fetching data from the combined file")
    #     with h5py.File(combined_file, 'r') as h5in:
    #         for epoch in h5in.keys():
    #             if epoch not in rawdata:
    #                 rawdata[epoch] = {}
    #                 df_rawdata[epoch] = {}
    #             for wave_type in h5in[epoch].keys():
    #                 if wave_type not in rawdata:
    #                     rawdata[epoch][wave_type] = {}
    #                     df_rawdata[epoch][wave_type] = {}
    #                 for r_in in h5in[epoch][wave_type].keys():
    #                     for r_out in h5in[epoch][wave_type][r_in].keys():
    #                         group = h5in[epoch][wave_type][str(r_in)][str(r_out)]
    #                         if 'computed_psf' in group:
    #                             r_in = int(r_in)
    #                             r_out = int(r_out)

    #                             if r_in not in rawdata[epoch][wave_type]:
    #                                 rawdata[epoch][wave_type][r_in] = {}
    #                             if r_out not in rawdata[epoch][wave_type][r_in]:
    #                                 rawdata[epoch][wave_type][r_in][r_out] = {}

    #                             if r_in not in df_rawdata[epoch][wave_type]:
    #                                 df_rawdata[epoch][wave_type][r_in] = {}
    #                             if r_out not in df_rawdata[epoch][wave_type][r_in]:
    #                                 df_rawdata[epoch][wave_type][r_in][r_out] = {}

    #                             if str(epoch)+"_"+str(r_in)+"_"+str(r_out) not in dataList:
    #                                 dataList.append(str(epoch)+"_"+str(r_in)+"_"+str(r_out))
    #                             phase_values_sorted = np.array(
    #                                 group['computed_psf']['phase_values_sorted'])
    #                             time_sorted = np.array(
    #                                 group['computed_psf']['time_sorted'])
    #                             psf_flux_sorted = np.array(
    #                                 group['computed_psf']['psf_flux_sorted'])
    #                             psf_flux_unc_sorted = np.array(
    #                                 group['computed_psf']['psf_flux_unc_sorted'])
    #                             frame_sorted = np.array(
    #                                 group['computed_psf']['frame_sorted'])
    #                             customdata_sorted = np.array(
    #                                 group['computed_psf']['customdata_phase'])
    #                             customdata_sorted_objects = [
    #                                 {**json.loads(item.decode('utf-8')), "time": Time(json.loads(
    #                                     item.decode('utf-8'))["mjd"], format="mjd", scale="tdb").datetime.strftime('%Y-%m-%d %H:%M:%S.%f')[:-5]}
    #                                 for item in customdata_sorted
    #                             ]

    #                             time = Time(
    #                                 np.array(group['computed_psf']['time']), format="mjd", scale="tdb")
    #                             time_mjd = np.array(group['computed_psf']['time'])
    #                             time_second = np.array(
    #                                 group['computed_psf']['time_second'])
    #                             time_minute = np.array(
    #                                 group['computed_psf']['time_minute'])
    #                             time_hour = np.array(
    #                                 group['computed_psf']['time_hour'])
    #                             time_day = np.array(
    #                                 group['computed_psf']['time_day'])
    #                             phase_values = np.array(
    #                                 group['computed_psf']['phase_values'])
    #                             psf_flux_time = np.array(
    #                                 group['computed_psf']['psf_flux_time'])
    #                             psf_flux_unc_time = np.array(
    #                                 group['computed_psf']['psf_flux_unc_time'])
    #                             frame = np.array(group['computed_psf']['frame'])
    #                             customdata_time = np.array(
    #                                 group['computed_psf']['customdata_time'])

    #                             customdata_time_objects = [
    #                                 {**json.loads(item.decode('utf-8')), "time": Time(json.loads(
    #                                     item.decode('utf-8'))["mjd"], format="mjd", scale="tdb").datetime.strftime('%Y-%m-%d %H:%M:%S.%f')[:-5]}
    #                                 for item in customdata_time
    #                             ]

    #                             phase_values_phase = np.concatenate(
    #                                 (phase_values_sorted, phase_values_sorted + 1))
    #                             time_mjd_phase = np.concatenate(
    #                                 (time_sorted, time_sorted))
    #                             psf_flux_phase = np.concatenate(
    #                                 (psf_flux_sorted, psf_flux_sorted))
    #                             psf_flux_unc_phase = np.concatenate(
    #                                 (psf_flux_unc_sorted, psf_flux_unc_sorted))
    #                             frame_phase = np.concatenate(
    #                                 (frame_sorted, frame_sorted))
    #                             customdata_phase = np.concatenate(
    #                                 (customdata_sorted_objects, customdata_sorted_objects))

    #                             df_rawdata[epoch][wave_type][r_in][r_out] = {
    #                                 "time_mjd": time_mjd,
    #                                 "psf_flux_time": psf_flux_time,
    #                                 "psf_flux_unc_time": psf_flux_unc_time,
    #                             }

    #                             valid_mask_time = ~np.isnan(psf_flux_time)
    #                             valid_mask_phase = ~np.isnan(psf_flux_phase)

    #                             rawdata[epoch][wave_type][r_in][r_out] = {
    #                                 "time": np.array(time)[valid_mask_time],
    #                                 "time_mjd": np.array(time_mjd)[valid_mask_time],
    #                                 "time_second": np.array(time_second)[valid_mask_time],
    #                                 "time_minute": np.array(time_minute)[valid_mask_time],
    #                                 "time_hour": np.array(time_hour)[valid_mask_time],
    #                                 "time_day": np.array(time_day)[valid_mask_time],
    #                                 "phase_values": np.array(phase_values)[valid_mask_time],
    #                                 "psf_flux_time": np.array(psf_flux_time)[valid_mask_time],
    #                                 "psf_flux_unc_time": np.array(psf_flux_unc_time)[valid_mask_time],
    #                                 "frame": np.array(frame)[valid_mask_time],
    #                                 "customdata_time": np.array(customdata_time_objects)[valid_mask_time],

    #                                 "phase_values_phase": np.array(phase_values_phase)[valid_mask_phase],
    #                                 "time_mjd_phase": np.array(time_mjd_phase)[valid_mask_phase],
    #                                 "psf_flux_phase": np.array(psf_flux_phase)[valid_mask_phase],
    #                                 "psf_flux_unc_phase": np.array(psf_flux_unc_phase)[valid_mask_phase],
    #                                 "frame_phase": np.array(frame_phase)[valid_mask_phase],
    #                                 "customdata_phase": np.array(customdata_phase)[valid_mask_phase],
    #                             }
    #                     # print(r_in, r_out)
    #     data_for_df = pad_and_align_data(df_rawdata)
    #     # print(dataList)
    #     print("Data fetching complete")
    #     return rawdata, dataList, data_for_df
