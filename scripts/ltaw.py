#!/usr/bin/env python3

"""Performs various analysis of LAMMPS output simulation files.

This module is the main program that drives/invokes various analysis on
LAMMPS output simulation files and other derivative files of LAMMPS
output simulation files.

"""

import os,sys
from pathlib import Path

source_root = Path(__file__).resolve().parents[1] / "src"
if source_root.is_dir():
    sys.path.insert(0, str(source_root))

# Import MDAnalysis through this package first before importing NumPy, SciPy,
# or MDAnalysis directly. Capture and restore the scheduler-assigned CPU
# affinity mask during initial import; otherwise, underlying C/OpenMP/BLAS
# libraries will alter the process affinity and pin worker threads to a
# restricted core subset.
from lammps_trajectory_analysis_workspaces import MDAnalysis as mda

from lammps_trajectory_analysis_workspaces.ltaw_workspace_parser import (
    run as main,
)

if __name__ == "__main__":
    main()
