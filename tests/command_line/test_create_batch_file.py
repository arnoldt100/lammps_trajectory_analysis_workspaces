import importlib.util
import json
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


def test_main_passes_same_options_to_module_and_returns_them(
    batch_file_script, monkeypatch,
):
    options = FileParserOptions(
        Path("template.slurm"), Path("batch.slurm"), Path("replacements.json")
    )
    calls = []

    def fake_parse():
        calls.append(True)
        return options

    monkeypatch.setattr(batch_file_script, "parse_command_line_arguments", fake_parse)
    conversions = []
    monkeypatch.setattr(
        batch_file_script.json_file_parser, "create_output_file", conversions.append
    )

    assert batch_file_script._main() is options
    assert calls == [True]
    assert len(conversions) == 1
    assert conversions[0] is options


@pytest.mark.parametrize(
    "error",
    [
        ValueError("invalid replacement"),
        json.JSONDecodeError("invalid JSON", "{", 0),
        PermissionError("read denied"),
        OSError("write failed; failed to remove incomplete output: cleanup denied"),
        UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid byte"),
        UnicodeEncodeError("utf-8", "\ud800", 0, 1, "invalid surrogate"),
    ],
)
def test_main_reports_expected_conversion_errors(
    batch_file_script, arguments, monkeypatch, capsys, error,
):
    monkeypatch.setattr(sys, "argv", ["create_batch_file.py", *arguments])

    def fail(_options):
        raise error

    monkeypatch.setattr(batch_file_script.json_file_parser, "create_output_file", fail)

    with pytest.raises(SystemExit) as exc_info:
        batch_file_script._main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == f"create_batch_file.py: error: {error}\n"


def test_main_does_not_hide_unexpected_errors(
    batch_file_script, arguments, monkeypatch,
):
    monkeypatch.setattr(sys, "argv", ["create_batch_file.py", *arguments])

    def fail(_options):
        raise RuntimeError("unexpected failure")

    monkeypatch.setattr(batch_file_script.json_file_parser, "create_output_file", fail)

    with pytest.raises(RuntimeError, match="unexpected failure"):
        batch_file_script._main()


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
    assert "Existing output paths are never overwritten." in result.stdout
    assert "parses arguments only" not in result.stdout


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


@pytest.mark.parametrize("line_ending", [b"\n", b"\r\n"])
@pytest.mark.parametrize("final_newline", [False, True])
def test_standalone_script_generates_expected_output(
    invocation_directory, tmp_path, line_ending, final_newline,
):
    paths = [
        tmp_path / "template with spaces.slurm",
        tmp_path / "batch.slurm",
        tmp_path / "replacements.json",
    ]
    suffix = line_ending if final_newline else b""
    paths[0].write_bytes(
        b"#!/bin/bash" + line_ending
        + b"#SBATCH --job-name=__JOB__" + line_ending
        + b"echo __JOB__ __TIME__" + suffix
    )
    paths[2].write_text(
        '{"__JOB__": "analysis", "__TIME__": "01:00:00"}', encoding="utf-8"
    )
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
    assert paths[1].read_bytes() == (
        b"#!/bin/bash" + line_ending
        + b"#SBATCH --job-name=analysis" + line_ending
        + b"echo analysis 01:00:00" + suffix
    )


def test_standalone_script_accepts_data_assignment(tmp_path, invocation_directory):
    template = tmp_path / "template.slurm"
    output = tmp_path / "batch.slurm"
    replacements = tmp_path / "replacements.json"
    template.write_text("#SBATCH --job-name=__jobname__\n", encoding="utf-8")
    replacements.write_text('data = {"jobname": "PC-9-ar_small_box"}', encoding="utf-8")

    result = run_script(
        [
            "--input-file", str(template),
            "--output-file", str(output),
            "--json-file", str(replacements),
        ],
        invocation_directory,
    )

    assert result.returncode == 0
    assert result.stdout == result.stderr == ""
    assert output.read_text(encoding="utf-8") == "#SBATCH --job-name=PC-9-ar_small_box\n"


@pytest.mark.parametrize(
    ("text", "diagnostic"),
    [
        ('{"jobname": "x"}', "Replacement file must start with 'data ='"),
        ('data = {"jobname": }', "Expecting value"),
        ("data = []", "JSON replacements must be an object"),
        ('data = {"bad__name": "x"}', "Invalid placeholder key: 'bad__name'"),
        ('data = {"jobname": 1}', "Replacement for 'jobname' must be a string"),
    ],
)
@pytest.mark.parametrize("existing_output", [False, True])
def test_standalone_script_reports_schema_errors_without_touching_output(
    tmp_path, text, diagnostic, existing_output,
):
    template = tmp_path / "template.slurm"
    output = tmp_path / "batch.slurm"
    replacements = tmp_path / "replacements.json"
    template.write_text("__jobname__", encoding="utf-8")
    replacements.write_text(text, encoding="utf-8")
    if existing_output:
        output.write_bytes(b"existing output")

    result = run_script(
        [
            "--input-file", str(template),
            "--output-file", str(output),
            "--json-file", str(replacements),
        ],
        tmp_path,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert diagnostic in result.stderr
    assert "Traceback" not in result.stderr
    assert template.read_text(encoding="utf-8") == "__jobname__"
    assert replacements.read_text(encoding="utf-8") == text
    if existing_output:
        assert output.read_bytes() == b"existing output"
    else:
        assert not output.exists()


def test_standalone_script_leaves_existing_files_unchanged(tmp_path):
    contents = {
        "template.slurm": b"__JOB_NAME__",
        "batch.slurm": b"existing output",
        "replacements.json": b'{"__JOB_NAME__": "analysis"}',
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

    assert result.returncode == 1
    assert result.stdout == ""
    assert "create_batch_file.py: error:" in result.stderr
    assert "File exists" in result.stderr
    assert "Traceback" not in result.stderr
    assert {path.name: path.read_bytes() for path in tmp_path.iterdir()} == contents


@pytest.mark.parametrize(
    ("failure", "diagnostic"),
    [
        ("missing-input", "No such file"),
        ("missing-json", "No such file"),
        ("invalid-json", "Expecting"),
        ("non-object-json", "must be an object"),
        ("invalid-key", "Invalid placeholder key"),
        ("non-string-value", "must be a string"),
        ("missing-replacement", "Missing replacement"),
        ("invalid-utf8-input", "codec can't decode"),
        ("invalid-utf8-json", "codec can't decode"),
        ("invalid-utf8-output", "codec can't encode"),
        ("missing-parent", "No such file"),
        ("output-symlink", "File exists"),
        ("dangling-symlink", "File exists"),
        ("output-is-input", "File exists"),
        ("output-is-json", "File exists"),
    ],
)
def test_standalone_script_reports_conversion_failures(
    tmp_path, failure, diagnostic,
):
    input_path = tmp_path / "template.slurm"
    json_path = tmp_path / "replacements.json"
    output_path = tmp_path / "batch.slurm"
    input_path.write_bytes(b"__JOB__")
    json_path.write_bytes(b'{"__JOB__": "analysis"}')

    if failure == "missing-input":
        input_path.unlink()
    elif failure == "missing-json":
        json_path.unlink()
    elif failure == "invalid-json":
        json_path.write_bytes(b"{")
    elif failure == "non-object-json":
        json_path.write_bytes(b"[]")
    elif failure == "invalid-key":
        json_path.write_bytes(b'{"JOB": "analysis"}')
    elif failure == "non-string-value":
        json_path.write_bytes(b'{"__JOB__": 42}')
    elif failure == "missing-replacement":
        json_path.write_bytes(b"{}")
    elif failure == "invalid-utf8-input":
        input_path.write_bytes(b"\xff")
    elif failure == "invalid-utf8-json":
        json_path.write_bytes(b"\xff")
    elif failure == "invalid-utf8-output":
        json_path.write_bytes(b'{"__JOB__": "\\ud800"}')
    elif failure == "missing-parent":
        output_path = tmp_path / "missing" / "batch.slurm"
    elif failure == "output-symlink":
        output_path.symlink_to(input_path)
    elif failure == "dangling-symlink":
        output_path.symlink_to(tmp_path / "missing")
    elif failure == "output-is-input":
        output_path = input_path
    elif failure == "output-is-json":
        output_path = json_path

    originals = {
        path: path.read_bytes()
        for path in (input_path, json_path)
        if path.exists()
    }
    original_link = output_path.readlink() if output_path.is_symlink() else None
    result = run_script(
        [
            "--input-file", str(input_path),
            "--output-file", str(output_path),
            "--json-file", str(json_path),
        ],
        tmp_path,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert "create_batch_file.py: error:" in result.stderr
    assert diagnostic in result.stderr
    assert "Traceback" not in result.stderr
    assert all(path.read_bytes() == content for path, content in originals.items())
    if original_link is not None:
        assert output_path.readlink() == original_link
    elif output_path not in originals:
        assert not output_path.exists()


def test_standalone_script_resolves_relative_paths_from_working_directory(tmp_path):
    (tmp_path / "template.slurm").write_bytes(b"__JOB__")
    (tmp_path / "replacements.json").write_bytes(b'{"__JOB__": "analysis"}')

    result = run_script(
        [
            "--input-file", "template.slurm",
            "--output-file", "batch.slurm",
            "--json-file", "replacements.json",
        ],
        tmp_path,
    )

    assert result.returncode == 0
    assert result.stdout == result.stderr == ""
    assert (tmp_path / "batch.slurm").read_bytes() == b"analysis"
