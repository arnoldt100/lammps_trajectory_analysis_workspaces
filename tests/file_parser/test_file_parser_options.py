from dataclasses import fields, is_dataclass
from pathlib import Path

import pytest

from lammps_trajectory_analysis_workspaces.file_parser import FileParserOptions
from lammps_trajectory_analysis_workspaces.file_parser.file_parser_options import (
    FileParserOptions as ModuleFileParserOptions,
)


def test_package_exports_file_parser_options():
    assert FileParserOptions is ModuleFileParserOptions


def test_file_parser_options_contains_required_paths():
    options = FileParserOptions(
        input_file=Path("template.slurm"),
        output_file=Path("batch.slurm"),
        json_file=Path("replacements.json"),
    )

    assert is_dataclass(options)
    assert [field.name for field in fields(options)] == [
        "input_file",
        "output_file",
        "json_file",
    ]
    assert options.input_file == Path("template.slurm")
    assert options.output_file == Path("batch.slurm")
    assert options.json_file == Path("replacements.json")
    assert all(
        isinstance(getattr(options, field.name), Path)
        for field in fields(options)
    )
    assert not options.input_file.is_absolute()
    assert not options.output_file.is_absolute()
    assert not options.json_file.is_absolute()


@pytest.mark.parametrize("missing_field", ["input_file", "output_file", "json_file"])
def test_file_parser_options_requires_every_path(missing_field):
    arguments = {
        "input_file": Path("template.slurm"),
        "output_file": Path("batch.slurm"),
        "json_file": Path("replacements.json"),
    }
    del arguments[missing_field]

    with pytest.raises(TypeError, match=missing_field):
        FileParserOptions(**arguments)
