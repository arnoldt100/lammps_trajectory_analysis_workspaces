import importlib.util
import subprocess
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


def test_main_returns_parsed_options(batch_file_script, monkeypatch):
    options = FileParserOptions(
        Path("template.slurm"), Path("batch.slurm"), Path("replacements.json")
    )
    calls = []

    def fake_parse():
        calls.append(True)
        return options

    monkeypatch.setattr(batch_file_script, "parse_command_line_arguments", fake_parse)

    assert batch_file_script._main() is options
    assert calls == [True]


@pytest.fixture(params=["repository", "external"])
def invocation_directory(request, tmp_path):
    if request.param == "repository":
        return Path(__file__).parents[2]
    return tmp_path


def run_script(arguments, working_directory):
    script_path = Path(__file__).parents[2] / "scripts" / "create_batch_file.py"
    return subprocess.run(
        [sys.executable, "-I", str(script_path), *arguments],
        cwd=working_directory,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


@pytest.mark.parametrize("help_option", ["-h", "--help"])
def test_standalone_script_displays_help(help_option, invocation_directory):
    result = run_script([help_option], invocation_directory)

    assert result.returncode == 0
    assert result.stderr == ""
    assert "usage:" in result.stdout
    assert "-h, --help" in result.stdout
    assert "--input-file INPUT_FILE" in result.stdout
    assert "--output-file OUTPUT_FILE" in result.stdout
    assert "--json-file JSON_FILE" in result.stdout
    assert "Currently parses arguments only" in result.stdout


@pytest.mark.parametrize(
    ("omitted_option", "extra_arguments", "diagnostic"),
    [
        ("all", [], "required"),
        ("--input-file", [], "--input-file"),
        ("--output-file", [], "--output-file"),
        ("--json-file", [], "--json-file"),
        (None, ["--unknown"], "unrecognized arguments"),
        (None, ["--input", "other.slurm"], "unrecognized arguments"),
    ],
)
def test_standalone_script_reports_argument_errors(
    arguments, invocation_directory, omitted_option, extra_arguments, diagnostic,
):
    if omitted_option == "all":
        arguments = []
    elif omitted_option is not None:
        index = arguments.index(omitted_option)
        del arguments[index:index + 2]

    result = run_script([*arguments, *extra_arguments], invocation_directory)

    assert result.returncode == 2
    assert result.stdout == ""
    assert diagnostic in result.stderr


def test_standalone_script_parses_without_creating_files(
    invocation_directory, tmp_path,
):
    paths = [
        tmp_path / "missing template.slurm",
        tmp_path / "batch.slurm",
        tmp_path / "missing.json",
    ]
    result = run_script(
        [
            "--input-file", str(paths[0]),
            "--output-file", str(paths[1]),
            "--json-file", str(paths[2]),
        ],
        invocation_directory,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""
    assert list(tmp_path.iterdir()) == []


def test_standalone_script_leaves_existing_files_unchanged(tmp_path):
    contents = {
        "template.slurm": b"\xff__JOB_NAME__",
        "batch.slurm": b"existing output",
        "replacements.json": b"not valid JSON",
    }
    for name, content in contents.items():
        (tmp_path / name).write_bytes(content)

    result = run_script(
        [
            "--input-file", "template.slurm",
            "--output-file", "batch.slurm",
            "--json-file", "replacements.json",
        ],
        tmp_path,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""
    assert {path.name: path.read_bytes() for path in tmp_path.iterdir()} == contents
