#! /usr/bin/env python3

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

source_root = Path(__file__).resolve().parents[1] / "src"
if source_root.is_dir():
    sys.path.insert(0, str(source_root))

from lammps_trajectory_analysis_workspaces.file_parser import FileParserOptions


def parse_command_line_arguments(
    argv: Sequence[str] | None = None,
) -> FileParserOptions:
    """Parse paths for batch-file generation without reading or writing files."""
    parser = argparse.ArgumentParser(
        description="Generate a Slurm batch file from a template and JSON replacements.",
        allow_abbrev=False,
    )
    parser.add_argument(
        "--input-file", type=Path, required=True, help="Path to the text template."
    )
    parser.add_argument(
        "--output-file", type=Path, required=True, help="Path for the generated batch file."
    )
    parser.add_argument(
        "--json-file", type=Path, required=True, help="Path to the JSON replacement map."
    )

    arguments = parser.parse_args(argv)
    return FileParserOptions(
        input_file=arguments.input_file,
        output_file=arguments.output_file,
        json_file=arguments.json_file,
    )


def _main():
    ...

if __name__ == "__main__":
    _main 
