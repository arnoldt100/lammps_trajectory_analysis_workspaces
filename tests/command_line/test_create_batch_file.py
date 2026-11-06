import importlib.util
import sys
from pathlib import Path

import pytest

from lammps_trajectory_analysis_workspaces.file_parser import FileParserOptions


@pytest.fixture
def batch_file_script(monkeypatch):
    monkeypatch.setattr(sys, "path", sys.path.copy())
    script_path = Path(__file__).parents[2] / "scripts" / "create_batch_file.py"
    spec = importlib.util.spec_from_file_location("create_batch_file", script_path)
    assert spec is not None
    assert spec.loader is not None
    script = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(script)
    return script


@pytest.fixture
def arguments():
    return [
        "--input-file", "template.slurm",
        "--output-file", "batch.slurm",
        "--json-file", "replacements.json",
    ]


@pytest.mark.parametrize("sequence_type", [list, tuple])
def test_parser_returns_file_parser_options(
    batch_file_script, arguments, sequence_type,
):
    options = batch_file_script.parse_command_line_arguments(sequence_type(arguments))

    assert isinstance(options, FileParserOptions)
    assert options == FileParserOptions(
        input_file=Path("template.slurm"),
        output_file=Path("batch.slurm"),
        json_file=Path("replacements.json"),
    )
    assert all(
        isinstance(path, Path)
        for path in (options.input_file, options.output_file, options.json_file)
    )


def test_parser_defaults_to_process_arguments(
    batch_file_script, arguments, monkeypatch,
):
    monkeypatch.setattr(sys, "argv", ["create_batch_file.py", *arguments])

    options = batch_file_script.parse_command_line_arguments()

    assert options.input_file == Path("template.slurm")
    assert options.output_file == Path("batch.slurm")
    assert options.json_file == Path("replacements.json")


@pytest.mark.parametrize("missing_option", [
    "--input-file", "--output-file", "--json-file",
])
def test_parser_requires_each_option(
    batch_file_script, arguments, missing_option, capsys,
):
    index = arguments.index(missing_option)
    del arguments[index:index + 2]

    with pytest.raises(SystemExit) as exc_info:
        batch_file_script.parse_command_line_arguments(arguments)

    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "required" in captured.err
    assert missing_option in captured.err


def test_parser_requires_all_options(batch_file_script, capsys):
    with pytest.raises(SystemExit) as exc_info:
        batch_file_script.parse_command_line_arguments([])

    assert exc_info.value.code == 2
    diagnostic = capsys.readouterr().err
    assert all(option in diagnostic for option in (
        "--input-file", "--output-file", "--json-file",
    ))


@pytest.mark.parametrize("option", ["--input-file", "--output-file", "--json-file"])
def test_parser_requires_an_option_value(
    batch_file_script, arguments, option, capsys,
):
    del arguments[arguments.index(option) + 1]

    with pytest.raises(SystemExit) as exc_info:
        batch_file_script.parse_command_line_arguments(arguments)

    assert exc_info.value.code == 2
    diagnostic = capsys.readouterr().err
    assert option in diagnostic
    assert "expected one argument" in diagnostic


@pytest.mark.parametrize("extra_argument", ["--unknown", "--input", "extra.slurm"])
def test_parser_rejects_unknown_arguments(
    batch_file_script, arguments, extra_argument, capsys,
):
    with pytest.raises(SystemExit) as exc_info:
        batch_file_script.parse_command_line_arguments([*arguments, extra_argument])

    assert exc_info.value.code == 2
    assert "unrecognized arguments" in capsys.readouterr().err


@pytest.mark.parametrize("help_option", ["-h", "--help"])
def test_parser_displays_help(batch_file_script, help_option, capsys):
    with pytest.raises(SystemExit) as exc_info:
        batch_file_script.parse_command_line_arguments([help_option])

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert "usage:" in captured.out
    assert "--input-file INPUT_FILE" in captured.out
    assert "--output-file OUTPUT_FILE" in captured.out
    assert "--json-file JSON_FILE" in captured.out


@pytest.mark.parametrize("absolute_paths", [False, True])
def test_parser_preserves_paths_without_file_io(
    batch_file_script, tmp_path, monkeypatch, capsys, absolute_paths,
):
    monkeypatch.chdir(tmp_path)
    paths = [Path("missing template.slurm"), Path("batch.slurm"), Path("missing.json")]
    if absolute_paths:
        paths = [tmp_path / path for path in paths]
    arguments = [
        "--input-file", str(paths[0]),
        "--output-file", str(paths[1]),
        "--json-file", str(paths[2]),
    ]
    options = batch_file_script.parse_command_line_arguments(arguments)

    assert options == FileParserOptions(*paths)
    assert list(tmp_path.iterdir()) == []
    assert capsys.readouterr() == ("", "")
