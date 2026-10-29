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


def test_process_command_line_arguments_rejects_unknown_argument(capsys):
    with pytest.raises(SystemExit) as exc_info:
        process_command_line_arguments(
            [
                "lop_sf_fcc_animation",
                "--input-file",
                "trajectory.h5",
                "--output-vtkhdf-file",
                "animation.vtkhdf",
                "--unknown-argument",
            ]
        )

    assert exc_info.value.code == 2
    assert "unrecognized arguments" in capsys.readouterr().err


def test_process_command_line_arguments_returns_cli_args_with_handler():
    cli_args = process_command_line_arguments(
        [
            "lop_sf_fcc_animation",
            "--input-file",
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


def test_animation_subcommand_handler_invokes_callable(tmp_path, capsys):
    input_file = tmp_path / "trajectory.h5"
    input_file.write_text("test data", encoding="utf-8")
    output_file = tmp_path / "animation.vtkhdf"
    cli_args = process_command_line_arguments(
        [
            "lop_sf_fcc_animation",
            "--input-file",
            str(input_file),
            "--output-vtkhdf-file",
            str(output_file),
        ]
    )

    cli_args.parsed_arguments.func(cli_args.parsed_arguments)

    assert capsys.readouterr().out == (
        f"Reading HDF5 trajectory from: {input_file}\n"
        f"Writing VTKHDF animation to: {output_file}\n"
    )


def test_animation_subcommand_handler_surfaces_missing_input(tmp_path, capsys):
    cli_args = process_command_line_arguments(
        [
            "lop_sf_fcc_animation",
            "--input-file",
            str(tmp_path / "missing.h5"),
            "--output-vtkhdf-file",
            str(tmp_path / "animation.vtkhdf"),
        ]
    )

    with pytest.raises(FileNotFoundError, match="input file does not exist"):
        cli_args.parsed_arguments.func(cli_args.parsed_arguments)

    assert capsys.readouterr().out == ""


def test_main_invokes_parsed_function(monkeypatch):
    script_path = (
        Path(__file__).parents[2]
        / "scripts"
        / "lammps_trajectory_analysis_workspaces.py"
    )
    spec = importlib.util.spec_from_file_location("ltaw_cli_entry_point", script_path)
    assert spec is not None
    assert spec.loader is not None
    entry_point = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(entry_point)

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
):
    import sys

    from lammps_trajectory_analysis_workspaces.lop_sf_fcc_animation import (
        LopSfFccAnimation,
    )

    script_path = (
        Path(__file__).parents[2]
        / "scripts"
        / "lammps_trajectory_analysis_workspaces.py"
    )
    spec = importlib.util.spec_from_file_location("ltaw_cli_dispatch", script_path)
    assert spec is not None
    assert spec.loader is not None
    entry_point = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(entry_point)

    input_file = tmp_path / "trajectory.h5"
    output_file = tmp_path / "animation.vtkhdf"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "program",
            "lop_sf_fcc_animation",
            "--input-file",
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
