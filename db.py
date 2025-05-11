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
from urllib.request import urlopen

def fetch_json(url):
    with urlopen(url) as r:
        return json.load(r)
    
current_directory = Path.cwd()

def get_db(database_name):
    client = MongoClient(config.MONGO_URI)
    db = client[database_name]
    return db

def close_db(client):
    client.close()

def get_data(db_name, rawdata, data_for_df, collection_name, isDB, epoch, wave_type, r_in, r_out):
    # normalize keys
    e = str(epoch)
    w = wave_type.lower()
    r1, r2 = str(r_in), str(r_out)
    id = f"{epoch}_{wave_type.lower()}_{r_in}_{r_out}"
    if isDB:
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
    else:
        # choose the right on-disk folder
        base = Path('./static/data/json/ZTF_J1539')
        sub = 'rawdata' if db_name == 'jwst_rawdata' else 'df'
        fp = base / sub / e / w / r1 / f"{r2}.json"

        if not fp.exists():
            raise KeyError(f"JSON file not found: {fp}")

        # load it
        data = json.loads(fp.read_text(encoding='utf-8'))

        # optionally cache for future calls
        # store = rawdata_dict if db_name == 'jwst_rawdata' else df_dict
        doc_id = f"{e}_{w}_{r1}_{r2}"
        # store[doc_id] = data
        return data
    # else:
    #     # base URL, not a Path
    #     base_url = (
    #         "https://raw.githubusercontent.com/"
    #         "iDataVisualizationLab/jwst-data/"
    #         "main/data/json/ZTF_J1539"
    #     )
    #     sub = "rawdata" if db_name == "jwst_rawdata" else "df"

    #     # build URL string
    #     url = f"{base_url}/{sub}/{e}/{w}/{r1}/{r2}.json"

    #     # fetch & return
    #     data = fetch_json(url)
    #     return data

        

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
        # with open('./static/ZTF_J1539/rawdata.json', 'r') as f:
        #     rawdata = json.load(f)
        with open('./static/data/json/ZTF_J1539/dataList.json', 'r') as f:
            cursor = json.load(f)
            for document in cursor:
                dataList.append({'label': document, 'value': document})
        # with open('./static/data/data_for_df.json', 'r') as f:
        #     data_for_df = json.load(f)
        print("Data fetching complete")
        return rawdata, dataList, data_for_df
    # elif not isDB:
    #     cursor = fetch_json('https://raw.githubusercontent.com/iDataVisualizationLab/jwst-data/main/data/json/ZTF_J1539/dataList.json')
    #     for document in cursor:
    #         dataList.append({'label': document, 'value': document})
    #     print("Data fetching complete")
    #     return rawdata, dataList, data_for_df

