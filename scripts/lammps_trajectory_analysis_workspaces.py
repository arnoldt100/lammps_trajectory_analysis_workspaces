#!/usr/bin/env python3

"""Performs various analysis of LAMMPS output simulation files.

This module is the main program that drives/invokes various analysis on
LAMMPS output simulation files and other derivative files of LAMMPS
output simulation files.

"""

import sys
from pathlib import Path

source_root = Path(__file__).resolve().parents[1] / "src"
if source_root.is_dir():
    sys.path.insert(0, str(source_root))

from lammps_trajectory_analysis_workspaces.cli_args import CLIArgs
from lammps_trajectory_analysis_workspaces.ltaw_workspace_parser import (
    process_command_line_arguments,
)


def main() -> CLIArgs:
    """Parse command-line arguments and dispatch the selected command."""
    cli_args = process_command_line_arguments()
    parsed_arguments = cli_args.parsed_arguments
    parsed_arguments.func(parsed_arguments)
    return cli_args

if __name__ == "__main__":
    main()
