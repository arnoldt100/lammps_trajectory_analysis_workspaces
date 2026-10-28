import argparse
import importlib.util
from pathlib import Path

import pytest

from lammps_trajectory_analysis_workspaces.cli_args import CLIArgs
from lammps_trajectory_analysis_workspaces.ltaw_workspace_parser import (
    process_command_line_arguments,
)


@pytest.mark.parametrize("argv", [[], ()])
def test_process_command_line_arguments_returns_cli_args(argv):
    cli_args = process_command_line_arguments(argv)

    assert isinstance(cli_args, CLIArgs)
    assert isinstance(cli_args.parsed_arguments, argparse.Namespace)


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
        process_command_line_arguments(["--unknown-argument"])

    assert exc_info.value.code == 2
    assert "unrecognized arguments" in capsys.readouterr().err


def test_main_calls_argument_processor_and_returns_its_result(monkeypatch):
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

    expected_cli_args = CLIArgs(parsed_arguments=argparse.Namespace())
    calls = []

    def fake_process_command_line_arguments():
        calls.append(True)
        return expected_cli_args

    monkeypatch.setattr(
        entry_point,
        "process_command_line_arguments",
        fake_process_command_line_arguments,
    )

    assert entry_point.main() is expected_cli_args
    assert calls == [True]
