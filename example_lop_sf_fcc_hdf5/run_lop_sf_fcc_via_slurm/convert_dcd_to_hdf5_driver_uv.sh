#! /usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail
shopt -s extglob nullglob

declare -r nm_tasks=1
declare -r nm_cpus_per_task=2
declare -r nm_workers=2
declare -r jobname="PC-9-ar_small_box"
declare -r jobname_long="PC-9-0-ar_small_box-solid_liquid-double_precision-79.0K-79.0K"
declare -r tag=${nm_tasks}.${nm_cpus_per_task}.${nm_workers}
declare -r in_file="convert_dcd_to_hdf5_via_uv.slurm"
declare -r slurm_batch_file=out_uv.${jobname}.${tag}.slurm
unset PYTHON_GIL
rm -f ${slurm_batch_file}
uv run create_batch_file.py --input-file ${in_file} \
  --output-file ${slurm_batch_file} --json-file job_parameters.json
sbatch ${slurm_batch_file}
