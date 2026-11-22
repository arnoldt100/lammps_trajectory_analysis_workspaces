#! /usr/bin/env bash
#SBATCH -A stf006
#SBATCH -J __jobname__.__nm_tasks__.__nm_cpus_per_task__.__nm_workers__
#SBATCH -t __wall_time__
#SBATCH -o __jobname__.__nm_tasks__.__nm_cpus_per_task__.__nm_workers__.stdout
#SBATCH -e __jobname__.__nm_tasks__.__nm_cpus_per_task__.__nm_workers__.stderr
#SBATCH -p __batch__
#SBATCH -N __nm_nodes__
#SBATCH --exclusive

# Riker Slurm batch script.

echo "Slurm script start time: $(date)"

export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OMP_PROC_BIND=false

# ----------------------------------------------------
# Source file "slurm_script_utilities.sh"  which
# contains many reusable slurm helper functions.
# ----------------------------------------------------
source ${SLURM_UTILITIES_SCRIPT_DIR}/slurm_script_utilities.sh

# ----------------------------------------------------
# Source file "slurm_olcf_mpich_omp_settings.sh" which defines OLCF
# environmental variables for OpenMP and Cray MPICH.
# ----------------------------------------------------
source ${SLURM_UTILITIES_SCRIPT_DIR}/slurm_olcf_mpich_omp_settings.sh

# ----------------------------------------------------
# Declare the top level batch launch directory.
#
# This  directory contains the LAMMPS input files and slurm batch file. The
# slurm sbatch command is executed form this directory.
# ----------------------------------------------------
declare -r batch_launch_directory="${SLURM_SUBMIT_DIR}"

# ----------------------------------------------------
# Define the variable SCRIPT_PATH for the path to this
# Slurm batch file.
# ----------------------------------------------------
SCRIPT_PATH=$(slurm_script_path)

# ----------------------------------------------------
# Define the variable SCRIPT_NAME for the name of this
# Slurm batch file.
# ----------------------------------------------------
SCRIPT_NAME=$(slurm_script_name)

echo "The script path is: $SCRIPT_PATH"
echo "The script name is: $SCRIPT_NAME"

# ----------------------------------------------------
# Activate the Python virtual environment.
# ----------------------------------------------------
unset PYTHON_GIL
source "${LTAT_PYTHON_VENV}"/bin/activate
export UV_PROJECT_ENVIRONMENT=/lustre/orion/proj-shared/stf006/arnoldt/sw/Python_Virtual_Environments/riker-ltat-venv

# ----------------------------------------------------
# Define the variable LTAT_DEBUG_PLOT_FRAMES for the
# number of DCD trajectory to convert to HDF5 entries.
# If nm_frames_to_write=-1, then all frames will be written.
# If nm_frames_to_write is a positive integer N, i.e. 1, 2, 3, ...,
# then N frames will be written.
# ----------------------------------------------------
declare -r nm_frames_to_write="__nm_frames_to_write__"
if [[ "${nm_frames_to_write}" =~ ^[+-]?[[:digit:]]+$ ]]; then
    echo "Writing ${nm_frames_to_write} DCD trajectories to HDF5 file."
else
    echo "Warning! The variable nm_frames_to_write has a value that is not an integer."
    echo "  nm_frames_to_write=${nm_frames_to_write}"
    exit 1
fi 
export LTAT_DEBUG_PLOT_FRAMES=${nm_frames_to_write}

# ----------------------------------------------------
# Define the variable for the cluster scratch space
# to do the actual file conversion.
# ----------------------------------------------------
declare -r scratchspace="${LTAW_SCRATCH_SPACE}/convert_dcd_to_vtkhdf/__jobname_long__/${SLURM_JOB_ID}"

# ----------------------------------------------------
# Forcibly create the worksapce.
# ----------------------------------------------------
slurm_force_mkdir ${scratchspace}

# -----------------
# No user changes required below this comment.
# -----------------

# ----------------------------------------------------
# Define the variable BIN for the absolute path to the Python module that
# converts the LAMMPS DCD to a HDF5 file.
# ----------------------------------------------------
declare -r BIN="${LTAT_TOP_LEVEL}/src/bin/lammps_analysis_tool.py"
declare -r PYTHONBIN="$(which python3)"

# ----------------------------------------------------
# Define the variables for the options of the command
# "uv run lammps_analysis_tool.py lop_sf_fcc".
# ----------------------------------------------------
declare -r dcd_file_name=__dcd_filename__
declare -r trajectory_file=__dcd_filename__
declare -r psf_file=__psf_file__
declare -r edge_length=__edge_length__
declare -r output_hdf5=__output_hdf5__
declare -r timeunits=__timeunits__
declare -r dt=__dt__
declare -r cutoff=__cutoff__
declare -r nm_tasks=__nm_tasks__
declare -r nm_nodes=__nm_nodes__
declare -r nm_workers=__nm_workers__
declare -r nm_cpus_per_task=__nm_cpus_per_task__
declare -r md_params_json=__md_params_json__
declare -r md_params_metadata_json=__md_params_metadata_json__
declare -r md_metadata_schema_json=__md_metadata_schema_json__

cp -f ${SCRIPT_PATH} ${scratchspace}
cp -f ${dcd_file_name} ${scratchspace}
cp -f ${psf_file} ${scratchspace}
cp -f ${md_params_json} ${scratchspace}
cp -f ${md_params_metadata_json} ${scratchspace}
cp -f ${md_metadata_schema_json} ${scratchspace}

cd ${scratchspace}

echo "Python binary: $(which python3)"

echo "Cpus_allowed_list:  $(grep Cpus_allowed_list /proc/self/status)"
echo 
echo 
echo "Writing cores available by python -c"
srun -n ${nm_tasks} -c ${nm_cpus_per_task} --cpu-bind=cores ${PYTHONBIN} -c 'import os; import multiprocessing; print(f"os.sched_getaffinity(0): {os.sched_getaffinity(0)}",flush=True); print(f"multiprocessing.cpu_count(): {multiprocessing.cpu_count()}",flush=True)'

echo
echo
echo "Slurm workload manager job id: ${SLURM_JOB_ID}"
echo "Number tasks: ${nm_tasks}"
echo "Number cpus per task: ${nm_cpus_per_task}"
echo "Number workes: ${nm_workers}"
echo "Scratch workspace: ${scratchspace}"
echo "Started running program"
srun -n ${nm_tasks} -c ${nm_cpus_per_task} --cpu-bind=cores \
  uv run ${BIN} lop_sf_fcc --trajectory ${dcd_file_name} \
  --psf ${psf_file} --edge-length ${edge_length} --timeunits ${timeunits} --dt ${dt} \
  --cutoff ${cutoff} --output-hdf5-file ${output_hdf5} \
  --parallel-threads=${nm_workers} --md-params-json ${md_params_json}
echo "Finished running program"

echo "Slurm script finish time: $(date)"
