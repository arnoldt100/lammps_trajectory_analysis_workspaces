#!/usr/bin/env python3

"""Performs various analysis of LAMMPS output simulation files.

This module is the main program that drives/invokes various analysis on
LAMMPS output simulation files and other derivative files of LAMMPS
output simulation files.

"""

import sys
from pathlib import Path

source_root = Path(__file__).resolve().parent / "src"
if source_root.is_dir():
    sys.path.insert(0, str(source_root))

from lammps_trajectory_analysis_workspaces.ltaw_workspace_parser import (
    run as main,
)


if __name__ == "__main__":
    main()
