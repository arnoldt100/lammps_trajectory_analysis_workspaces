"""Typed container for parsed command-line arguments."""

from argparse import Namespace
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CLIArgs:
    """Hold values parsed by the command-line interface."""

    parsed_arguments: Namespace
