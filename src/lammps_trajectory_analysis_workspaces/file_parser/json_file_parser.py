"""Validate JSON replacements, render templates, and create output files."""

import json
import re

from lammps_trajectory_analysis_workspaces.file_parser.file_parser_options import (
    FileParserOptions,
)


_PLACEHOLDER = re.compile(r"__(.*?)__")


def _render_template(template: str, json_text: str) -> str:
    """Apply validated JSON replacements literally, without file I/O."""
    decoded: object = json.loads(json_text)
    if not isinstance(decoded, dict):
        raise ValueError("JSON replacements must be an object")

    replacements: dict[str, str] = {}
    for key, value in decoded.items():
        if not isinstance(key, str) or _PLACEHOLDER.fullmatch(key) is None:
            raise ValueError(f"Invalid placeholder key: {key!r}")
        if not isinstance(value, str):
            raise ValueError(f"Replacement for {key!r} must be a string")
        replacements[key] = value

    def replace(match: re.Match[str]) -> str:
        placeholder = match.group(0)
        if placeholder not in replacements:
            raise ValueError(f"Missing replacement for placeholder {placeholder!r}")
        return replacements[placeholder]

    return _PLACEHOLDER.sub(replace, template)


def create_output_file(options: FileParserOptions) -> None:
    """Render UTF-8 sources and exclusively create output after validation.

    Byte I/O preserves line endings without platform newline translation.
    Validation, decoding, and encoding finish before output creation.
    Filesystem errors propagate; failed writes remove the incomplete output.
    """
    template = options.input_file.read_bytes().decode("utf-8")
    json_text = options.json_file.read_bytes().decode("utf-8")
    output_bytes = _render_template(template, json_text).encode("utf-8")

    output = options.output_file.open("xb")
    try:
        with output:
            output.write(output_bytes)
    except OSError as write_error:
        try:
            options.output_file.unlink()
        except OSError as cleanup_error:
            raise OSError(
                f"{write_error}; failed to remove incomplete output "
                f"{str(options.output_file)!r}: {cleanup_error}"
            ) from cleanup_error
        raise
