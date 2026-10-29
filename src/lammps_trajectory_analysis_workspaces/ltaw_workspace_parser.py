"""Create and process the command-line parser."""

import argparse
from collections.abc import Sequence

from lammps_trajectory_analysis_workspaces.cli_args import CLIArgs
from lammps_trajectory_analysis_workspaces.cli import (
    add_lop_sf_fcc_animation_subparser,
)


def process_command_line_arguments(
    argv: Sequence[str] | None = None,
) -> CLIArgs:
    """Parse command-line arguments and return them in a ``CLIArgs`` object.

    The top-level parser supports argparse's built-in help options and
    registered task subcommands. The selected subcommand and its parsed
    arguments are available through ``CLIArgs.parsed_arguments``.
    """
    parser = argparse.ArgumentParser(
        description="Analyze LAMMPS simulation output and generate plots."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    add_lop_sf_fcc_animation_subparser(subparsers)

    parsed_arguments = parser.parse_args(argv)
    return CLIArgs(parsed_arguments=parsed_arguments)
