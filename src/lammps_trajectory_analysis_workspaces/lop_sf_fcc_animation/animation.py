"""Callable boundary for generating a LOP-SF-FCC animation."""

from argparse import Namespace
from pathlib import Path

from lammps_trajectory_analysis_tools.lib.lop_sf_fcc_vtkhdf_writer import (
    HDF5LopSfFccAnimationSourceBuilderKey,
    LopSfFccVtkhdfAnimationConverter,
    LopSfFccVtkhdfAnimationConverterBuilderKey,
    LopSfFccVtkhdfAnimationSourceInterface,
    lop_sf_fcc_vtkhdf_animation_writer_factory,
)


class LopSfFccAnimation:
    """Represent conversion of an HDF5 trajectory to a VTKHDF animation."""

    __slots__ = ("_input_file", "_output_vtkhdf_file")

    def __init__(
        self,
        input_file: Path,
        output_vtkhdf_file: Path,
    ) -> None:
        """Validate and retain the input and output paths."""
        if not isinstance(input_file, Path):
            raise TypeError("input_file must be a pathlib.Path")
        if not input_file.exists():
            raise FileNotFoundError(f"input file does not exist: {input_file}")
        if not input_file.is_file():
            raise ValueError(f"input file is not a regular file: {input_file}")
        if not isinstance(output_vtkhdf_file, Path):
            raise TypeError("output_vtkhdf_file must be a pathlib.Path")

        self._input_file = input_file
        self._output_vtkhdf_file = output_vtkhdf_file

    @property
    def input_file(self) -> Path:
        """Return the input HDF5 trajectory path."""
        return self._input_file

    @property
    def output_vtkhdf_file(self) -> Path:
        """Return the output VTKHDF animation path."""
        return self._output_vtkhdf_file

    def __call__(self) -> None:
        """Read the HDF5 trajectory and write its VTKHDF animation."""
        self._read_hdf5_file()
        self._write_vtkhdf_file()

    def _read_hdf5_file(self) -> None:
        """Validate and stream the input trajectory through LTAT's reader."""
        source: LopSfFccVtkhdfAnimationSourceInterface = (
            lop_sf_fcc_vtkhdf_animation_writer_factory.build(
                HDF5LopSfFccAnimationSourceBuilderKey,
                file_path=self._input_file,
            )
        )
        with source:
            # Decoding validates each frame without retaining the trajectory.
            for _ in source.frames():
                pass

    def _write_vtkhdf_file(self) -> None:
        """Write the animation through LTAT's builder-backed converter."""
        converter: LopSfFccVtkhdfAnimationConverter = (
            lop_sf_fcc_vtkhdf_animation_writer_factory.build(
                LopSfFccVtkhdfAnimationConverterBuilderKey,
            )
        )
        converter.convert_hdf5(self._input_file, self._output_vtkhdf_file)

    @staticmethod
    def run_from_cli_args(arguments: Namespace) -> None:
        """Construct and invoke an animation from parsed CLI arguments."""
        animation = LopSfFccAnimation(
            input_file=arguments.input_file,
            output_vtkhdf_file=arguments.output_vtkhdf_file,
        )
        animation()
