#!/usr/bin/env python3

"""Performs various analysis of LAMMPS output simulation files.

This module is the main program that drives/invokes various analysis on
LAMMPS output simulation files and other derivative files of LAMMPS
output simulation files.

"""

from lammps_trajectory_analysis_workspaces.cli_args import CLIArgs
from lammps_trajectory_analysis_workspaces.ltaw_workspace_parser import (
    process_command_line_arguments,
)


def main() -> CLIArgs:
    """Parse command-line arguments and return the parsed values."""
    return process_command_line_arguments()

if __name__ == "__main__":
    main()
