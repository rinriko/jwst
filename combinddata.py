import h5py
import re

# List of LW and SW files
sw_files = [
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch1.sw.10.30.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch1.sw.10.40.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch1.sw.10.50.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch1.sw.10.60.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch1.sw.14.30.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch1.sw.14.40.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch1.sw.14.50.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch1.sw.14.60.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch1.sw.18.30.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch1.sw.18.40.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch1.sw.18.50.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch1.sw.18.60.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch1.sw.22.30.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch1.sw.22.40.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch1.sw.22.50.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch1.sw.22.60.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch1.sw.26.30.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch1.sw.26.40.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch1.sw.26.50.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch1.sw.26.60.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch1.sw.30.40.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch1.sw.30.50.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch1.sw.30.60.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch2.sw.10.30.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch2.sw.10.40.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch2.sw.10.50.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch2.sw.10.60.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch2.sw.14.30.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch2.sw.14.40.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch2.sw.14.50.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch2.sw.14.60.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch2.sw.18.30.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch2.sw.18.40.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch2.sw.18.50.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch2.sw.18.60.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch2.sw.22.30.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch2.sw.22.40.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch2.sw.22.50.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch2.sw.22.60.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch2.sw.26.30.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch2.sw.26.40.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch2.sw.26.50.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch2.sw.26.60.hdf5",
    "T:\jwst\static\data\Shaw_ZTF_J1539_photometry.epoch2.sw.30.40.hdf5",
    "T:\jwst\static\data\Shaw_ZTF_J1539_photometry.epoch2.sw.30.50.hdf5",
    "T:\jwst\static\data\Shaw_ZTF_J1539_photometry.epoch2.sw.30.60.hdf5"
]
lw_files = [
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch1.lw.10.30.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch1.lw.10.40.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch1.lw.10.50.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch1.lw.10.60.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch1.lw.14.30.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch1.lw.14.40.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch1.lw.14.50.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch1.lw.14.60.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch1.lw.18.30.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch1.lw.18.40.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch1.lw.18.50.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch1.lw.18.60.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch1.lw.22.30.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch1.lw.22.40.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch1.lw.22.50.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch1.lw.22.60.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch1.lw.26.30.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch1.lw.26.40.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch1.lw.26.50.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch1.lw.26.60.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch1.lw.30.40.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch1.lw.30.50.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch1.lw.30.60.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch2.lw.10.30.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch2.lw.10.40.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch2.lw.10.50.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch2.lw.10.60.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch2.lw.14.30.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch2.lw.14.40.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch2.lw.14.50.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch2.lw.14.60.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch2.lw.18.30.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch2.lw.18.40.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch2.lw.18.50.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch2.lw.18.60.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch2.lw.22.30.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch2.lw.22.40.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch2.lw.22.50.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch2.lw.22.60.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch2.lw.26.30.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch2.lw.26.40.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch2.lw.26.50.hdf5",
    "T:/jwst/static/data/Shaw_ZTF_J1539_photometry.epoch2.lw.26.60.hdf5",
    "T:\jwst\static\data\Shaw_ZTF_J1539_photometry.epoch2.lw.30.40.hdf5",
    "T:\jwst\static\data\Shaw_ZTF_J1539_photometry.epoch2.lw.30.50.hdf5",
    "T:\jwst\static\data\Shaw_ZTF_J1539_photometry.epoch2.lw.30.60.hdf5"
]


# Combine LW and SW files
all_files = lw_files + sw_files

# Output file name
# output_file = "combined_photometry_psf.hdf5"
output_file = "combined_photometry_computed_psf.hdf5"

def get_params(file_name):
    """Extract parameters from the file name using regex."""
    # Adjust the regex pattern to match the epoch, wave type, and parameters
    match = re.search(r'\.epoch(\d+)\.(lw|sw)\.(\d+)\.(\d+)\.hdf5$', file_name)
    if match:
        epoch, wave_type, r_in, r_out = match.groups()
        return epoch, wave_type, r_in, r_out
    return None, None, None, None

# Create the output HDF5 file
with h5py.File(output_file, 'w') as h5out:
    for file in all_files:
        epoch, wave_type, r_in, r_out = get_params(file)
        if not (epoch and wave_type and r_in and r_out):
            continue  # Skip files with unrecognized patterns
        group_name = f"epoch{epoch}/{wave_type}/{r_in}/{r_out}"
        
        # with h5py.File(file, 'r') as h5in:
        #     if 'psf' in h5in:
        #         # Create groups and copy the 'psf' dataset
        #         group = h5out.require_group(group_name)
        #         h5in.copy('psf', group, name='psf')
        
        with h5py.File(file, 'r') as h5in:
            if 'computed_psf' in h5in:
                # Create groups and copy the 'psf' dataset
                group = h5out.require_group(group_name)
                h5in.copy('computed_psf', group, name='computed_psf')

# print(f"All 'psf' datasets have been combined into {output_file}")
print(f"All 'computed_psf' datasets have been combined into {output_file}")
