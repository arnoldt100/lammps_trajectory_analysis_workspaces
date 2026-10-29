"""Build the ``lop_sf_fcc_animation`` command-line subparser."""

import argparse
from pathlib import Path

from lammps_trajectory_analysis_workspaces.lop_sf_fcc_animation import (
    LopSfFccAnimation,
)


def add_lop_sf_fcc_animation_subparser(
    subparsers: argparse._SubParsersAction,
) -> argparse.ArgumentParser:
    """Add the LOP-SF-FCC animation command and return its parser."""
    parser = subparsers.add_parser(
        "lop_sf_fcc_animation",
        help="Convert an HDF5 trajectory file to a VTKHDF animation file.",
        description=(
            "Convert an HDF5 trajectory file to a VTKHDF animation file."
        ),
    )
    parser.add_argument(
        "--input-file",
        type=Path,
        required=True,
        help="Path to the input HDF5 trajectory file.",
    )
    parser.add_argument(
        "--output-vtkhdf-file",
        type=Path,
        required=True,
        help="Path for the output VTKHDF animation file.",
    )
    parser.set_defaults(func=LopSfFccAnimation.run_from_cli_args)
    return parser
