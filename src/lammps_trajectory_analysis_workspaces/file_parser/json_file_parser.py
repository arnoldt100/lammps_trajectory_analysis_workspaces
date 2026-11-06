"""Validate JSON replacements, render templates, and create output files."""

import json
import re
from importlib.resources import files

from jsonschema import Draft202012Validator

from lammps_trajectory_analysis_workspaces.file_parser.file_parser_options import (
    FileParserOptions,
)


_PLACEHOLDER = re.compile(r"__(.*?)__")
_DATA_ASSIGNMENT = re.compile(r"\s*data\s*=\s*")
_SCHEMA = json.loads(
    files(__package__).joinpath("replacements.schema.json").read_text(encoding="utf-8")
)
Draft202012Validator.check_schema(_SCHEMA)
_VALIDATOR = Draft202012Validator(_SCHEMA)


def _render_template(template: str, json_text: str) -> str:
    """Apply validated JSON replacements literally, without file I/O."""
    assignment = _DATA_ASSIGNMENT.match(json_text)
    if assignment is None:
        raise ValueError("Replacement file must start with 'data ='")
    decoded = json.loads(json_text[assignment.end():])
    error = next(_VALIDATOR.iter_errors(decoded), None)
    if error is not None:
        schema_path = tuple(error.absolute_schema_path)
        if schema_path == ("type",):
            detail = "JSON replacements must be an object"
        elif schema_path[0] == "propertyNames":
            detail = f"Invalid placeholder key: {error.instance!r}"
        elif schema_path == ("additionalProperties", "type") and error.absolute_path:
            detail = f"Replacement for {error.absolute_path[0]!r} must be a string"
        else:
            detail = error.message
        raise ValueError(f"Invalid JSON replacements: {detail}") from error

    replacements: dict[str, str] = {
        f"__{key}__": value for key, value in decoded.items()
    }

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
