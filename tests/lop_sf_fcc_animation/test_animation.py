from pathlib import Path
from unittest.mock import MagicMock, call

import pytest

from lammps_trajectory_analysis_tools.data_writer_utils.exceptions import (
    DataWriterConfigurationError,
    DataWriterTargetError,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc_vtkhdf_writer import (
    HDF5LopSfFccAnimationSourceBuilderKey,
    LopSfFccVtkhdfAnimationConverter,
    LopSfFccVtkhdfAnimationConverterBuilderKey,
    LopSfFccVtkhdfAnimationSourceInterface,
    lop_sf_fcc_vtkhdf_animation_writer_factory,
)
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


def test_call_reads_hdf5_then_converts(tmp_path, capsys, monkeypatch):
    input_file = tmp_path / "trajectory.h5"
    input_file.write_text("test data", encoding="utf-8")
    animation = LopSfFccAnimation(
        input_file,
        tmp_path / "animation.vtkhdf",
    )
    events = []
    source = MagicMock(spec=LopSfFccVtkhdfAnimationSourceInterface)

    def frames():
        for index in range(3):
            events.append(index)
            yield object()

    source.frames.side_effect = frames
    converter = MagicMock(spec=LopSfFccVtkhdfAnimationConverter)
    build = MagicMock(side_effect=[source, converter])
    monkeypatch.setattr(lop_sf_fcc_vtkhdf_animation_writer_factory, "build", build)

    def convert(source_path, target_path):
        assert source_path == input_file
        assert target_path == animation.output_vtkhdf_file
        assert events == [0, 1, 2]
        source.__exit__.assert_called_once_with(None, None, None)

    converter.convert_hdf5.side_effect = convert

    result = animation()

    assert result is None
    assert build.call_args_list == [
        call(HDF5LopSfFccAnimationSourceBuilderKey, file_path=input_file),
        call(LopSfFccVtkhdfAnimationConverterBuilderKey),
    ]
    converter.convert_hdf5.assert_called_once_with(
        input_file, animation.output_vtkhdf_file
    )
    source.__enter__.assert_called_once_with()
    assert capsys.readouterr().out == ""
    assert not animation.output_vtkhdf_file.exists()


@pytest.mark.parametrize("failure_stage", ["build", "convert"])
def test_write_failure_propagates(tmp_path, monkeypatch, failure_stage):
    input_file = tmp_path / "trajectory.h5"
    input_file.write_text("test data", encoding="utf-8")
    animation = LopSfFccAnimation(input_file, tmp_path / "animation.vtkhdf")
    converter = MagicMock(spec=LopSfFccVtkhdfAnimationConverter)
    build = MagicMock(return_value=converter)
    error = DataWriterTargetError("conversion failed")
    if failure_stage == "build":
        build.side_effect = error
    else:
        converter.convert_hdf5.side_effect = error
    monkeypatch.setattr(lop_sf_fcc_vtkhdf_animation_writer_factory, "build", build)

    with pytest.raises(DataWriterTargetError) as exc_info:
        animation._write_vtkhdf_file()

    assert exc_info.value is error
    build.assert_called_once_with(LopSfFccVtkhdfAnimationConverterBuilderKey)
    if failure_stage == "build":
        converter.convert_hdf5.assert_not_called()
    else:
        converter.convert_hdf5.assert_called_once_with(
            input_file, animation.output_vtkhdf_file
        )


@pytest.mark.parametrize("failure_stage", ["build", "open", "iterate"])
def test_read_failure_propagates_without_writing(tmp_path, monkeypatch, failure_stage):
    input_file = tmp_path / "trajectory.h5"
    input_file.write_text("test data", encoding="utf-8")
    animation = LopSfFccAnimation(input_file, tmp_path / "animation.vtkhdf")
    source = MagicMock(spec=LopSfFccVtkhdfAnimationSourceInterface)
    build = MagicMock(return_value=source)
    write = MagicMock()
    error = (
        DataWriterConfigurationError("invalid frame")
        if failure_stage == "iterate"
        else DataWriterTargetError("reader failed")
    )
    if failure_stage == "build":
        build.side_effect = error
    elif failure_stage == "open":
        source.__enter__.side_effect = error
    else:
        def frames():
            yield object()
            raise error

        source.frames.side_effect = frames
    monkeypatch.setattr(lop_sf_fcc_vtkhdf_animation_writer_factory, "build", build)
    monkeypatch.setattr(LopSfFccAnimation, "_write_vtkhdf_file", write)

    with pytest.raises(type(error)) as exc_info:
        animation()

    assert exc_info.value is error
    write.assert_not_called()
    if failure_stage == "iterate":
        source.__exit__.assert_called_once()
        assert source.__exit__.call_args.args[1] is error
    else:
        source.__exit__.assert_not_called()
    assert not animation.output_vtkhdf_file.exists()
