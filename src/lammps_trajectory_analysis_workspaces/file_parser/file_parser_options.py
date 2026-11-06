"""Typed options for template conversion."""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class FileParserOptions:
    input_file: Path
    output_file: Path
    json_file: Path
