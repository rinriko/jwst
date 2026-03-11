# save_as_json_and_reload.py

import json, gzip
from pathlib import Path
from typing import Dict, Any, Union
import numpy as np
from pymongo import MongoClient
import config


def process_data(collection_name: str) -> Dict[str, Any]:
    """
    Builds a nested dict: rawdata[epoch][wave_type][r_in][r_out][filename][frame] = [x, y]
    All keys are strings and values are JSON-safe.
    """
    rawdata: Dict[str, Any] = {}

    print("Fetching data from MongoDB...")
    client = MongoClient(config.MONGO_LOCAL_URI)
    db = client["jwst"]
    collection = db[collection_name]

    epochs = collection.distinct("epoch")
    for epoch in epochs:
        epoch_key = str(epoch)
        rawdata.setdefault(epoch_key, {})

        types = collection.distinct("type", {"epoch": epoch})
        for wave_type in types:
            wt_key = str(wave_type)
            rawdata[epoch_key].setdefault(wt_key, {})

            r_in_values = collection.distinct("r_in", {"epoch": epoch, "type": wave_type})
            for r_in in r_in_values:
                r_in_key = str(r_in)
                rawdata[epoch_key][wt_key].setdefault(r_in_key, {})

                r_out_values = collection.distinct(
                    "r_out",
                    {"epoch": epoch, "type": wave_type, "r_in": r_in}
                )
                for r_out in r_out_values:
                    r_out_key = str(r_out)
                    rawdata[epoch_key][wt_key][r_in_key].setdefault(r_out_key, {})

                    cursor = collection.find(
                        {"epoch": epoch, "type": wave_type, "r_in": r_in, "r_out": r_out}
                    )
                    target = rawdata[epoch_key][wt_key][r_in_key][r_out_key]
                    for doc in cursor:
                        if "aperture" not in doc:
                            continue

                        frames    = np.array(doc["aperture"]["frame"])
                        filenames = np.array(doc["aperture"]["filename"])
                        xcenters  = np.array(doc["aperture"]["xcenter"])
                        ycenters  = np.array(doc["aperture"]["ycenter"])

                        for fn, fr, x, y in zip(filenames, frames, xcenters, ycenters):
                            fn_key = str(fn)
                            fr_key = str(fr)   # JSON object keys must be strings
                            xy_val = [float(x), float(y)]  # store as list, not tuple

                            if fn_key not in target:
                                target[fn_key] = {}
                            target[fn_key][fr_key] = xy_val

    return rawdata


def save_json(obj: Dict[str, Any], path: Union[str, Path], gzip_compress: bool = False) -> Path:
    """
    Save dict as JSON (optionally gzipped).
    """
    path = Path(path)
    if gzip_compress:
        if path.suffix != ".gz":
            path = path.with_suffix(path.suffix + ".gz")
        with gzip.open(path, "wt", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)
    else:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)
    return path


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


# -------- Example usage --------
# 1) Build from Mongo
# 2) Save to JSON or JSON.GZ
# 3) Load back and use

if __name__ == "__main__":
    # Build
    rawdata = process_data("ZTF_J1539")

    # Save (pick one)
    out_path = save_json(rawdata, "rawdata.json", gzip_compress=False)
    # out_path = save_json(rawdata, "rawdata.json.gz", gzip_compress=True)

    print(f"Saved to: {out_path}")

    # Load back
    data2 = load_json(out_path)
    print("Loaded JSON. Example access:")

    # Example: iterate and print one (epoch, wave_type, r_in, r_out, filename, frame) entry
    # (Protect against empty dicts)
    for epoch_key, d1 in data2.items():
        for wt_key, d2 in d1.items():
            for r_in_key, d3 in d2.items():
                for r_out_key, d4 in d3.items():
                    for fn_key, frames_dict in d4.items():
                        for fr_key, xy_val in frames_dict.items():
                            print(
                                f"epoch={epoch_key} type={wt_key} r_in={r_in_key} r_out={r_out_key} "
                                f"file={fn_key} frame={fr_key} xy={xy_val}"
                            )
                            raise SystemExit  # just show one example
