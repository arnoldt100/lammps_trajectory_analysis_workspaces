# Running lammps_analyis_tool/py lop_fcc_sf via Slurm Workload Manager

There are 4 files that need editing:

    * job_parameters.json
    * convert_dcd_hdf5_driver_via_uv.sh
    * convert_dcd_hdf5_via_uv.slurm 

These files generally do not need editing

    * argon_box_small.psf
    * PC-9-0-ar_small_box-solid_liquid-double_precision-79.0K-79.0K.all.dcd
    * md_params_metadata.json
    * md_metadata.schema.json

This is a JSON file used to substitute its values into a slurm batch template file.

In general a key-value data "<some_key>" : "<a_value>" will replace the text
__some_key__ in file convert_dcd_hdf5_via_uv.slurm with "a_value". A specific
example is the key-value entry "wall_time" : "00:10:00" will replace all
occurrences of the text "__wall_time__" in file convert_dcd_hdf5_via_uv.slurm
with "00:10:00". 

## Important JSON Keys for Parallelization

| Key                | Description |
| -----              | -----       |
| "nm_frames_to_write" |  The number of frames to write to the HDF5 file. Must be an integer value. |
| "nm_cpus_per_task  | The number of cpus to used for the backend Python multiprocessing parallelization |
| "nm_works  | The number of workers for the backend Python multiprocessing parallelization. Set nm_workers equal nm_cpus_per_task. |


## convert_dcd_hdf5_driver_via_uv.sh

This bash program drives the creation and submission of a Slurm batch file.

Define the variables in this file, "convert_dcd_hdf5_driver_via_uv.sh", to have 
the same values as the corresponding variables in file "job_parameters.json".

## convert_dcd_hdf5_via_uv.slurm

This file is used a template for forming the Slurm batch file.

Ensure this template Slurm batch script has all of the keys found
in  job_parameters.json. Otherwise an error will be raised by program
"create_batch_file.py".

## PC-9-0-ar_small_box-solid_liquid-double_precision-79.0K-79.0K.all.dcd

This is the LAMMPS molecular simulation DCD trajectory file. This file is not
staged in the repository due to its large size.

## argon_box_small.psf

This is the Protein Structure File (PSF) that contains the topology information
of the LAMMPS DCD trajectory file.

## md_params_metadata.json

This JSON file contains the metadata about the simulation.

## md_metadata.schema.json

The JSON schema file "md_metadata.schema.json" is the validator for these
simulation metadata files.


