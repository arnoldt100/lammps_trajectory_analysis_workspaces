from pathlib import Path

import pytest

from lammps_trajectory_analysis_workspaces.lop_sf_fcc_animation import (
    LopSfFccAnimation,
)


def test_animation_retains_input_and_output_paths(tmp_path):
    input_file = tmp_path / "trajectory.h5"
    input_file.write_text("test data", encoding="utf-8")
    output_file = tmp_path / "animation.vtkhdf"

    animation = LopSfFccAnimation(input_file, output_file)

    assert animation.input_file == input_file
    assert animation.output_vtkhdf_file == output_file


def test_animation_requires_input_file_to_exist(tmp_path):
    with pytest.raises(FileNotFoundError, match="input file does not exist"):
        LopSfFccAnimation(tmp_path / "missing.h5", tmp_path / "animation.vtkhdf")


def test_animation_rejects_input_directory(tmp_path):
    with pytest.raises(ValueError, match="not a regular file"):
        LopSfFccAnimation(tmp_path, tmp_path / "animation.vtkhdf")


def test_animation_requires_path_arguments(tmp_path):
    input_file = tmp_path / "trajectory.h5"
    input_file.write_text("test data", encoding="utf-8")

    with pytest.raises(TypeError, match="input_file must be a pathlib.Path"):
        LopSfFccAnimation(str(input_file), tmp_path / "animation.vtkhdf")

    with pytest.raises(
        TypeError,
        match="output_vtkhdf_file must be a pathlib.Path",
    ):
        LopSfFccAnimation(input_file, str(tmp_path / "animation.vtkhdf"))


def test_call_prints_conversion_message(tmp_path, capsys):
    input_file = tmp_path / "trajectory.h5"
    input_file.write_text("test data", encoding="utf-8")
    animation = LopSfFccAnimation(
        input_file,
        tmp_path / "animation.vtkhdf",
    )

    result = animation()

    assert result is None
    assert capsys.readouterr().out == "converting HDF5 to VTKHDF\n"
