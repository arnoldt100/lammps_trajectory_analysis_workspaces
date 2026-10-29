from datetime import UTC, datetime
from hashlib import file_digest, sha256
from os import environ
from pathlib import Path
from subprocess import run

import h5py
import numpy as np
import pytest

from lammps_trajectory_analysis_tools.data_writer_utils.exceptions import (
    DataWriterConfigurationError,
    DataWriterTargetError,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.hdf5_writer import (
    HDF5LopSfFccTrajectoryWriterValueObjectBuilderKey,
    lop_sf_fcc_data_writer_factory,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc_vtkhdf_writer import (
    HDF5LopSfFccAnimationSourceBuilderKey,
    LopSfFccVtkhdfAnimationSourceInterface,
    LopSfFccVtkhdfAnimationWriter,
    lop_sf_fcc_vtkhdf_animation_writer_factory,
)
from lammps_trajectory_analysis_workspaces.lop_sf_fcc_animation import (
    LopSfFccAnimation,
)


@pytest.fixture
def trajectory_file(tmp_path: Path) -> Path:
    path = tmp_path / "trajectory.hdf5"
    writer = lop_sf_fcc_data_writer_factory.build(
        HDF5LopSfFccTrajectoryWriterValueObjectBuilderKey,
        file_path=path,
        metadata={
            "time_step": 0.5,
            "time_units_label": "ps",
            "number_of_trajectories": 3,
            "generation_date": datetime(2026, 10, 29, tzinfo=UTC),
            "compiler_build_flags": ("-O3",),
            "generating_machine": "test-host",
            "lmod_modules": ("gcc/14",),
        },
        layout={
            "number_of_atoms": 3,
            "length_units_label": "angstrom",
        },
    )
    with writer:
        for index, step in enumerate((10, 20, 30)):
            writer.append_trajectory_frames(
                index,
                np.asarray([step], dtype=np.int64),
                np.arange(9, dtype=np.float64).reshape(1, 3, 3) + index,
                np.asarray([[0.1, 0.2, 0.3]], dtype=np.float64),
                np.asarray([[10.0, 11.0, 12.0]], dtype=np.float64),
                np.asarray([[90.0, 90.0, 90.0]], dtype=np.float64),
            )
    return path


def test_reads_real_trajectory_repeatedly_without_modifying_input(
    trajectory_file: Path, tmp_path: Path, capsys,
):
    original_digest = sha256(trajectory_file.read_bytes()).digest()
    output = tmp_path / "animation.vtkhdf"
    animation = LopSfFccAnimation(trajectory_file, output)

    for _ in range(2):
        assert animation._read_hdf5_file() is None

    assert capsys.readouterr().out == ""
    assert sha256(trajectory_file.read_bytes()).digest() == original_digest
    assert not output.exists()


def test_local_ten_trajectory_sample(tmp_path: Path):
    sample_path = environ.get("LTAW_SAMPLE_HDF5")
    if sample_path is None:
        pytest.skip("Set LTAW_SAMPLE_HDF5 to run the local 10-trajectory sample check")
    input_file = Path(sample_path)
    with input_file.open("rb") as handle:
        original_digest = file_digest(handle, "sha256").hexdigest()
    source: LopSfFccVtkhdfAnimationSourceInterface = (
        lop_sf_fcc_vtkhdf_animation_writer_factory.build(
            HDF5LopSfFccAnimationSourceBuilderKey,
            file_path=input_file,
        )
    )
    with source:
        assert source.frame_count == 10
        atom_count = source.layout.number_of_atoms
        time_step = source.metadata.time_step
        time_units = source.metadata.time_units_label
        length_units = source.metadata.length_units_label
        count = 0
        first_step = None
        previous_step = None
        for frame in source.frames():
            assert previous_step is None or frame.step_number > previous_step
            assert frame.positions.shape == (atom_count, 3)
            assert frame.lop_sf_fcc_values.shape == (atom_count,)
            assert frame.box_lengths.shape == (3,)
            assert frame.box_angles.shape == (3,)
            if first_step is None:
                first_step = frame.step_number
            previous_step = frame.step_number
            count += 1
        assert count == 10

    output = tmp_path / "sample-animation.vtkhdf"
    assert LopSfFccAnimation(input_file, output)() is None

    with source, h5py.File(output, "r") as target:
        metadata = target["LOPSFFCC"].attrs
        assert metadata["time_step"] == pytest.approx(time_step)
        assert metadata["time_units_label"] == time_units
        assert metadata["length_units_label"] == length_units
        vtkhdf = target["VTKHDF"]
        assert vtkhdf.attrs["Type"] == np.bytes_("PolyData")
        assert vtkhdf["Steps"].attrs["NSteps"] == count
        assert vtkhdf["Points"].shape == (count * atom_count, 3)
        assert vtkhdf["PointData"]["lop_sf_fcc"].shape == (count * atom_count,)
        np.testing.assert_array_equal(
            vtkhdf["NumberOfPoints"][:], np.full(count, atom_count)
        )
        compared = 0
        for index, frame in enumerate(source.frames()):
            start = index * atom_count
            stop = start + atom_count
            assert vtkhdf["FieldData"]["step_number"][index] == frame.step_number
            assert vtkhdf["Steps"]["Values"][index] == pytest.approx(
                frame.step_number * time_step
            )
            np.testing.assert_array_equal(
                vtkhdf["Points"][start:stop], frame.positions
            )
            np.testing.assert_array_equal(
                vtkhdf["PointData"]["lop_sf_fcc"][start:stop],
                frame.lop_sf_fcc_values,
            )
            np.testing.assert_array_equal(
                vtkhdf["FieldData"]["box_lengths"][index], frame.box_lengths
            )
            np.testing.assert_array_equal(
                vtkhdf["FieldData"]["box_angles"][index], frame.box_angles
            )
            compared += 1
        assert compared == count

    with input_file.open("rb") as handle:
        assert file_digest(handle, "sha256").hexdigest() == original_digest
    assert not output.with_name(f"{output.name}.tmp").exists()
    print(
        f"Sample conversion verified: {count} frames, {atom_count} atoms, "
        f"steps {first_step}..{previous_step}, time_step={time_step} {time_units}, "
        f"length_units={length_units}, sha256={original_digest}"
    )


def test_non_hdf5_input_surfaces_reader_error(tmp_path: Path, capsys):
    input_file = tmp_path / "invalid.hdf5"
    input_file.write_text("not an HDF5 file", encoding="utf-8")
    output = tmp_path / "animation.vtkhdf"
    animation = LopSfFccAnimation(input_file, output)

    with pytest.raises(DataWriterTargetError, match="could not open HDF5 source"):
        animation()

    assert capsys.readouterr().out == ""
    assert input_file.read_text(encoding="utf-8") == "not an HDF5 file"
    assert not output.exists()


@pytest.mark.parametrize("input_kind", ["generated", "sample"])
def test_paraview_reads_animation(
    trajectory_file: Path, tmp_path: Path, input_kind: str,
):
    pvpython = environ.get("LTAW_PVPYTHON")
    if pvpython is None:
        pytest.skip("Set LTAW_PVPYTHON to run the ParaView reader check")
    input_file = trajectory_file
    if input_kind == "sample":
        sample_path = environ.get("LTAW_SAMPLE_HDF5")
        if sample_path is None:
            pytest.skip("Set LTAW_SAMPLE_HDF5 to check the local sample in ParaView")
        input_file = Path(sample_path)
    with input_file.open("rb") as handle:
        original_digest = file_digest(handle, "sha256").digest()
    output = tmp_path / "paraview-animation.vtkhdf"
    LopSfFccAnimation(input_file, output)()

    script = """
import sys
from pathlib import Path
import numpy as np
from vtkmodules.vtkCommonExecutionModel import vtkStreamingDemandDrivenPipeline
from vtkmodules.vtkIOHDF import vtkHDFReader
from vtkmodules.util.numpy_support import vtk_to_numpy

reader = vtkHDFReader()
errors = []
reader.AddObserver("ErrorEvent", lambda *args: errors.append("VTK reader error"))
reader.SetFileName(sys.argv[1])
assert reader.CanReadFile(sys.argv[1]) == 1
reader.UpdateInformation()
assert not errors, errors
times = reader.GetOutputInformation(0).Get(
    vtkStreamingDemandDrivenPipeline.TIME_STEPS()
)
assert times is not None
directory = Path(sys.argv[2])
np.save(directory / "times.npy", times)
for index, time in enumerate(times):
    reader.UpdateTimeStep(time)
    assert not errors, errors
    data = reader.GetOutputDataObject(0)
    assert data.IsA("vtkPolyData")
    assert data.GetNumberOfVerts() == data.GetNumberOfPoints()
    np.savez(
        directory / f"frame-{index}.npz",
        positions=vtk_to_numpy(data.GetPoints().GetData()),
        lop_sf_fcc=vtk_to_numpy(data.GetPointData().GetArray("lop_sf_fcc")),
        step_number=vtk_to_numpy(data.GetFieldData().GetArray("step_number")),
        box_lengths=vtk_to_numpy(data.GetFieldData().GetArray("box_lengths")),
        box_angles=vtk_to_numpy(data.GetFieldData().GetArray("box_angles")),
    )
print(f"VTK reader verified {len(times)} time steps")
"""
    run(
        ["uv", "run", "--locked", pvpython, "--no-mpi", "-c", script,
         str(output), str(tmp_path)],
        check=True,
        timeout=120,
    )
    times = np.load(tmp_path / "times.npy")
    source: LopSfFccVtkhdfAnimationSourceInterface = (
        lop_sf_fcc_vtkhdf_animation_writer_factory.build(
            HDF5LopSfFccAnimationSourceBuilderKey, file_path=input_file,
        )
    )
    with source:
        assert len(times) == source.frame_count
        for index, frame in enumerate(source.frames()):
            assert times[index] == pytest.approx(
                frame.step_number * source.metadata.time_step
            )
            with np.load(tmp_path / f"frame-{index}.npz") as actual:
                np.testing.assert_array_equal(actual["positions"], frame.positions)
                np.testing.assert_array_equal(
                    actual["lop_sf_fcc"], frame.lop_sf_fcc_values
                )
                np.testing.assert_array_equal(
                    actual["step_number"].reshape(-1), [frame.step_number]
                )
                np.testing.assert_array_equal(
                    actual["box_lengths"].reshape(-1), frame.box_lengths
                )
                np.testing.assert_array_equal(
                    actual["box_angles"].reshape(-1), frame.box_angles
                )
    with input_file.open("rb") as handle:
        assert file_digest(handle, "sha256").digest() == original_digest
    assert not output.with_name(f"{output.name}.tmp").exists()


@pytest.mark.parametrize("invalid_data", ["missing-dataset", "nonfinite-frame"])
def test_invalid_trajectory_fails_before_write_stub(
    trajectory_file: Path, tmp_path: Path, capsys, invalid_data: str,
):
    with h5py.File(trajectory_file, "r+") as source:
        last_frame = source["trajectories"]["traj_00002"]
        if invalid_data == "missing-dataset":
            del last_frame["lop_sf_fcc"]
        else:
            last_frame["positions"][0, 0, 0] = np.nan
    original_digest = sha256(trajectory_file.read_bytes()).digest()
    output = tmp_path / "animation.vtkhdf"
    animation = LopSfFccAnimation(trajectory_file, output)
    message = "required datasets" if invalid_data == "missing-dataset" else "finite"

    with pytest.raises(DataWriterConfigurationError, match=message):
        animation()

    assert capsys.readouterr().out == ""
    assert sha256(trajectory_file.read_bytes()).digest() == original_digest
    assert not output.exists()


def test_conversion_preserves_trajectory_data(
    trajectory_file: Path, tmp_path: Path,
):
    original_digest = sha256(trajectory_file.read_bytes()).digest()
    output = tmp_path / "animation.vtkhdf"

    assert LopSfFccAnimation(trajectory_file, output)() is None

    with h5py.File(output, "r") as target:
        metadata = target["LOPSFFCC"].attrs
        assert metadata["time_step"] == pytest.approx(0.5)
        assert metadata["time_units_label"] == "ps"
        assert metadata["length_units_label"] == "angstrom"
        assert metadata["generating_machine"] == "test-host"
        vtkhdf = target["VTKHDF"]
        assert vtkhdf.attrs["Type"] == np.bytes_("PolyData")
        assert vtkhdf["Steps"].attrs["NSteps"] == 3
        np.testing.assert_array_equal(
            vtkhdf["FieldData"]["step_number"][:], [10, 20, 30]
        )
        np.testing.assert_allclose(vtkhdf["Steps"]["Values"][:], [5.0, 10.0, 15.0])
        np.testing.assert_array_equal(vtkhdf["NumberOfPoints"][:], [3, 3, 3])
        np.testing.assert_allclose(
            vtkhdf["Points"][:],
            np.concatenate([
                np.arange(9, dtype=np.float64).reshape(3, 3) + index
                for index in range(3)
            ]),
        )
        np.testing.assert_allclose(
            vtkhdf["PointData"]["lop_sf_fcc"][:], np.tile([0.1, 0.2, 0.3], 3)
        )
        np.testing.assert_allclose(
            vtkhdf["FieldData"]["box_lengths"][:],
            np.tile([10.0, 11.0, 12.0], (3, 1)),
        )
        np.testing.assert_allclose(
            vtkhdf["FieldData"]["box_angles"][:], np.full((3, 3), 90.0)
        )
    assert sha256(trajectory_file.read_bytes()).digest() == original_digest
    assert not output.with_name(f"{output.name}.tmp").exists()


def test_script_converts_trajectory(
    trajectory_file: Path, tmp_path: Path,
):
    original_digest = sha256(trajectory_file.read_bytes()).digest()
    output = tmp_path / "cli-animation.vtkhdf"
    result = run(
        [
            "uv", "run", "--project", str(Path(__file__).parents[2]), "--locked",
            str(Path(__file__).parents[2] / "scripts" / "ltaw.py"),
            "lop_sf_fcc_animation",
            str(trajectory_file), "--output-vtkhdf-file", str(output),
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=120,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout == ""
    with h5py.File(output, "r") as target:
        assert target["VTKHDF"]["Steps"].attrs["NSteps"] == 3
        np.testing.assert_array_equal(
            target["VTKHDF"]["Steps"]["Values"][:], [5.0, 10.0, 15.0]
        )
    assert sha256(trajectory_file.read_bytes()).digest() == original_digest
    assert not output.with_name(f"{output.name}.tmp").exists()


@pytest.mark.parametrize("existing_output", ["unrelated-file", "prior-conversion"])
def test_conversion_refuses_existing_output(
    trajectory_file: Path, tmp_path: Path, existing_output: str,
):
    input_digest = sha256(trajectory_file.read_bytes()).digest()
    output = tmp_path / "animation.vtkhdf"
    animation = LopSfFccAnimation(trajectory_file, output)
    if existing_output == "prior-conversion":
        animation()
    else:
        output.write_bytes(b"existing output must not be overwritten")
    output_digest = sha256(output.read_bytes()).digest()

    with pytest.raises(DataWriterTargetError, match="target already exists"):
        animation()

    assert sha256(output.read_bytes()).digest() == output_digest
    assert sha256(trajectory_file.read_bytes()).digest() == input_digest
    assert not output.with_name(f"{output.name}.tmp").exists()


def test_mid_write_failure_removes_staged_output(
    trajectory_file: Path, tmp_path: Path, monkeypatch,
):
    input_digest = sha256(trajectory_file.read_bytes()).digest()
    output = tmp_path / "animation.vtkhdf"
    staging = output.with_name(f"{output.name}.tmp")
    append_frames = LopSfFccVtkhdfAnimationWriter.append_frames
    error = DataWriterTargetError("injected write failure")
    appended = 0

    def failing_append(writer, *args, **kwargs):
        nonlocal appended
        assert staging.exists()
        if appended == 1:
            raise error
        append_frames(writer, *args, **kwargs)
        appended += 1

    monkeypatch.setattr(
        LopSfFccVtkhdfAnimationWriter, "append_frames", failing_append
    )

    with pytest.raises(DataWriterTargetError) as exc_info:
        LopSfFccAnimation(trajectory_file, output)()

    assert exc_info.value is error
    assert appended == 1
    assert not output.exists()
    assert not staging.exists()
    assert sha256(trajectory_file.read_bytes()).digest() == input_digest
