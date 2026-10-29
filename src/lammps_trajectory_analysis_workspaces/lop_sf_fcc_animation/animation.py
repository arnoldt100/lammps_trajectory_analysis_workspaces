"""Callable boundary for generating a LOP-SF-FCC animation."""

from argparse import Namespace
from pathlib import Path


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
        """Announce the pending HDF5-to-VTKHDF conversion."""
        print("converting HDF5 to VTKHDF")

    @staticmethod
    def run_from_cli_args(arguments: Namespace) -> None:
        """Construct and invoke an animation from parsed CLI arguments."""
        animation = LopSfFccAnimation(
            input_file=arguments.input_file,
            output_vtkhdf_file=arguments.output_vtkhdf_file,
        )
        animation()
