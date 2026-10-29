import argparse
import importlib.util
from pathlib import Path

import pytest

from lammps_trajectory_analysis_workspaces.cli.cli_args import CLIArgs
from lammps_trajectory_analysis_workspaces.ltaw_workspace_parser import (
    process_command_line_arguments,
)


@pytest.mark.parametrize("argv", [[], ()])
def test_process_command_line_arguments_requires_a_subcommand(argv):
    with pytest.raises(SystemExit) as exc_info:
        process_command_line_arguments(argv)

    assert exc_info.value.code == 2


@pytest.mark.parametrize("help_option", ["-h", "--help"])
def test_process_command_line_arguments_displays_help_and_exits(
    help_option,
    capsys,
):
    with pytest.raises(SystemExit) as exc_info:
        process_command_line_arguments([help_option])

    assert exc_info.value.code == 0
    assert "usage:" in capsys.readouterr().out


@pytest.fixture
def input_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    path = Path("trajectory.h5")
    path.write_text("test data", encoding="utf-8")
    return path


def test_process_command_line_arguments_rejects_unknown_argument(capsys, input_path):
    with pytest.raises(SystemExit) as exc_info:
        process_command_line_arguments(
            [
                "lop_sf_fcc_animation",
                "trajectory.h5",
                "--output-vtkhdf-file",
                "animation.vtkhdf",
                "--unknown-argument",
            ]
        )

    assert exc_info.value.code == 2
    assert "unrecognized arguments" in capsys.readouterr().err


def test_process_command_line_arguments_returns_cli_args_with_handler(input_path):
    cli_args = process_command_line_arguments(
        [
            "lop_sf_fcc_animation",
            "trajectory.h5",
            "--output-vtkhdf-file",
            "animation.vtkhdf",
        ]
    )

    assert isinstance(cli_args, CLIArgs)
    assert isinstance(cli_args.parsed_arguments, argparse.Namespace)
    assert cli_args.parsed_arguments.command == "lop_sf_fcc_animation"
    assert cli_args.parsed_arguments.input_file == Path("trajectory.h5")
    assert cli_args.parsed_arguments.output_vtkhdf_file == Path(
        "animation.vtkhdf"
    )
    assert callable(cli_args.parsed_arguments.func)


@pytest.mark.parametrize(
    ("arguments", "missing"),
    [
        (["--output-vtkhdf-file", "animation.vtkhdf"], "INPUT_FILE"),
        (["trajectory.h5"], "--output-vtkhdf-file"),
    ],
)
def test_animation_subcommand_requires_input_and_output(
    arguments, missing, capsys, input_path,
):
    with pytest.raises(SystemExit) as exc_info:
        process_command_line_arguments(["lop_sf_fcc_animation", *arguments])

    assert exc_info.value.code == 2
    assert missing in capsys.readouterr().err


def test_animation_subcommand_rejects_old_input_option(capsys, input_path):
    with pytest.raises(SystemExit) as exc_info:
        process_command_line_arguments(
            [
                "lop_sf_fcc_animation",
                "--input-file",
                "trajectory.h5",
                "--output-vtkhdf-file",
                "animation.vtkhdf",
            ]
        )

    assert exc_info.value.code == 2
    assert "unrecognized arguments: --input-file" in capsys.readouterr().err


def test_animation_subcommand_help_describes_positional_input(capsys):
    with pytest.raises(SystemExit) as exc_info:
        process_command_line_arguments(["lop_sf_fcc_animation", "--help"])

    assert exc_info.value.code == 0
    help_text = capsys.readouterr().out
    assert "INPUT_FILE" in help_text
    assert "--input-file" not in help_text
    assert "--output-vtkhdf-file" in help_text


def test_animation_subcommand_handler_invokes_callable(tmp_path, capsys, monkeypatch):
    from lammps_trajectory_analysis_workspaces.lop_sf_fcc_animation import (
        LopSfFccAnimation,
    )

    input_file = tmp_path / "trajectory.h5"
    input_file.write_text("test data", encoding="utf-8")
    output_file = tmp_path / "animation.vtkhdf"
    read_paths = []
    write_paths = []

    def read_stub(animation):
        read_paths.append(animation.input_file)

    def write_stub(animation):
        assert read_paths == [input_file]
        write_paths.append(animation.output_vtkhdf_file)

    monkeypatch.setattr(LopSfFccAnimation, "_read_hdf5_file", read_stub)
    monkeypatch.setattr(LopSfFccAnimation, "_write_vtkhdf_file", write_stub)
    cli_args = process_command_line_arguments(
        [
            "lop_sf_fcc_animation",
            str(input_file),
            "--output-vtkhdf-file",
            str(output_file),
        ]
    )

    cli_args.parsed_arguments.func(cli_args.parsed_arguments)

    assert read_paths == [input_file]
    assert write_paths == [output_file]
    assert capsys.readouterr().out == ""
    assert not output_file.exists()


@pytest.mark.parametrize(
    ("input_kind", "message"),
    [
        ("missing", "input file does not exist"),
        ("directory", "input file is not a regular file"),
        ("broken-symlink", "input file does not exist"),
    ],
)
def test_animation_subcommand_rejects_invalid_input(
    tmp_path, capsys, input_kind, message,
):
    input_file = tmp_path / "input.h5"
    if input_kind == "directory":
        input_file.mkdir()
    elif input_kind == "broken-symlink":
        input_file.symlink_to(tmp_path / "missing.h5")
    output = tmp_path / "animation.vtkhdf"
    with pytest.raises(SystemExit) as exc_info:
        process_command_line_arguments(
            [
                "lop_sf_fcc_animation",
                str(input_file),
                "--output-vtkhdf-file",
                str(output),
            ]
        )

    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert message in captured.err
    assert str(input_file) in captured.err
    assert not output.exists()


def test_animation_subcommand_accepts_symlink_to_regular_file(input_path, tmp_path):
    link = tmp_path / "linked.h5"
    link.symlink_to(input_path)
    cli_args = process_command_line_arguments(
        ["lop_sf_fcc_animation", str(link),
         "--output-vtkhdf-file", "animation.vtkhdf"]
    )

    assert cli_args.parsed_arguments.input_file == link


def test_animation_subcommand_revalidates_input_at_dispatch(input_path, capsys):
    cli_args = process_command_line_arguments(
        [
            "lop_sf_fcc_animation",
            str(input_path),
            "--output-vtkhdf-file",
            "animation.vtkhdf",
        ]
    )
    input_path.unlink()

    with pytest.raises(FileNotFoundError, match="input file does not exist"):
        cli_args.parsed_arguments.func(cli_args.parsed_arguments)

    assert capsys.readouterr().out == ""


@pytest.fixture
def entry_point():
    script_path = Path(__file__).parents[2] / "scripts" / "ltaw.py"
    spec = importlib.util.spec_from_file_location("ltaw_cli_entry_point", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_main_invokes_parsed_function(monkeypatch, entry_point):

    calls = []

    def fake_handler(arguments):
        calls.append(arguments)

    parsed_arguments = argparse.Namespace(func=fake_handler)
    expected_cli_args = CLIArgs(parsed_arguments=parsed_arguments)

    def fake_process_command_line_arguments():
        return expected_cli_args

    monkeypatch.setattr(
        entry_point,
        "process_command_line_arguments",
        fake_process_command_line_arguments,
    )

    assert entry_point.main() is expected_cli_args
    assert calls == [parsed_arguments]


def test_main_dispatches_animation_command_with_parsed_paths(
    monkeypatch,
    tmp_path,
    entry_point,
):
    import sys

    from lammps_trajectory_analysis_workspaces.lop_sf_fcc_animation import (
        LopSfFccAnimation,
    )

    input_file = tmp_path / "trajectory.h5"
    input_file.write_text("test data", encoding="utf-8")
    output_file = tmp_path / "animation.vtkhdf"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "program",
            "lop_sf_fcc_animation",
            str(input_file),
            "--output-vtkhdf-file",
            str(output_file),
        ],
    )
    calls = []

    def fake_handler(arguments):
        calls.append(arguments)

    monkeypatch.setattr(
        LopSfFccAnimation,
        "run_from_cli_args",
        staticmethod(fake_handler),
    )

    cli_args = entry_point.main()

    assert cli_args.parsed_arguments.command == "lop_sf_fcc_animation"
    assert cli_args.parsed_arguments.input_file == input_file
    assert cli_args.parsed_arguments.output_vtkhdf_file == output_file
    assert calls == [cli_args.parsed_arguments]
