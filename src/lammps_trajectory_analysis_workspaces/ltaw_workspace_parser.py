"""Create and process the command-line parser."""

import argparse
from collections.abc import Sequence

from lammps_trajectory_analysis_workspaces.cli_args import CLIArgs


def process_command_line_arguments(
    argv: Sequence[str] | None = None,
) -> CLIArgs:
    """Parse command-line arguments and return them in a ``CLIArgs`` object.

    The top-level parser currently supports only argparse's built-in help
    options. Task subcommands and their arguments will be added as tasks are
    defined.
    """
    parser = argparse.ArgumentParser(
        description="Analyze LAMMPS simulation output and generate plots."
    )
    parsed_arguments = parser.parse_args(argv)
    return CLIArgs(parsed_arguments=parsed_arguments)
