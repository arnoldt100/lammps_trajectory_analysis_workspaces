# File Parser Feature Workspace

## Feature Goal

Generate a Slurm batch file by replacing template placeholders with literal
string values from a JSON file.

Replacement files require `data =` followed by a JSON object with undelimited
keys, such as `"jobname"` for `__jobname__`. The object is checked against
the bundled JSON Schema; standalone JSON objects are rejected.

This ICM workspace tracks the plan and implementation status. Stage 1,
all three phases are implemented, verified, and approved, including
standalone invocation and parsing-only usage documentation. All 63 relevant
tests pass, including existing CLI regression tests.

Stage 2, Phase 1 adds in-memory JSON validation and literal template
substitution, with 49 focused tests, and is approved. Phase 2 adds safe file
handling with 41 additional tests and is approved. Phase 3 integrates CLI
conversion and documents complete usage; it is approved. The original
implementation passed 182 file-parser and CLI tests. The schema-checker
update is implemented and verified with 239 file-parser and command-line
tests, and awaits final review and approval.

## Implementation Stages

1. Add the shared options dataclass and implement and test a standalone
   parsing function that returns it.
2. Implement the JSON file module and pass the returned dataclass to it,
   then verify conversion and command-line error handling.

Stage 2 review phases:

1. JSON validation and in-memory substitution.
2. Safe file handling through `create_output_file(options)`.
3. CLI integration, command-line errors, end-to-end tests, and usage docs.

See the [implementation plan](top_level_plan.md) for stage boundaries and
completion criteria.

## Structural Boundaries

Planned production files:

- `scripts/create_batch_file.py`: standalone command-line entry point,
  `parse_command_line_arguments` returning `FileParserOptions`, delegation,
  and user-facing errors.
- `src/lammps_trajectory_analysis_workspaces/file_parser/__init__.py`:
  package boundary and re-export of `FileParserOptions`.
- `src/lammps_trajectory_analysis_workspaces/file_parser/file_parser_options.py`:
  shared `FileParserOptions` dataclass.
- `src/lammps_trajectory_analysis_workspaces/file_parser/json_file_parser.py`:
  JSON validation and template substitution (implemented in Stage 2,
  Phase 1), with safe output-file creation (implemented in Phase 2).

Planned tests:

- `tests/file_parser/test_file_parser_options.py`: shared options contract
  (implemented in Stage 1, Phase 1).
- `tests/file_parser/test_json_file_parser.py`: in-memory JSON validation
  and substitution (implemented in Stage 2, Phase 1), with file-handling
  coverage (implemented in Phase 2).
- `tests/file_parser/`: replacement behavior, validation, and file handling.
- `tests/command_line/test_create_batch_file.py`: parsing contract
  and standalone command behavior, including conversion, error diagnostics,
  exit status, and module delegation (updated in Stage 2, Phase 3).

The existing [`scripts/create_batch_file.py`](../../../scripts/create_batch_file.py)
parses arguments and passes the returned dataclass to the JSON module
through its main function and entry-point guard. It reports expected
conversion failures on stderr with exit status 1. See the
[project README](../../../README.md) for complete conversion usage.

## Library Conversion (Stage 2, Phase 2)

Programmatic callers can already create output through the library:

```python
from pathlib import Path

from lammps_trajectory_analysis_workspaces.file_parser import (
    FileParserOptions,
    json_file_parser,
)

options = FileParserOptions(
    input_file=Path("template.slurm"),
    output_file=Path("batch.slurm"),
    json_file=Path("replacements.json"),
)
json_file_parser.create_output_file(options)
```

The function returns `None`, leaves options unchanged, and prints nothing.
It decodes sources and encodes the completed result as UTF-8 before creating
output, preserving line endings and final-newline presence through byte I/O.
Existing output entries, including symlinks, are refused using exclusive
creation. The output parent directory must already exist.
JSON and replacement validation errors, encoding errors, and filesystem
errors propagate to the caller. A write or close failure removes the
incomplete output; a cleanup failure explicitly reports both failures.

## Dependencies and Relationships

- Inherits [project-wide rules](../../top_level_plan.md), including execution
  through `uv run`.
- Uses the `jsonschema` package to validate replacement objects.
- The standalone script delegates conversion to the
  file-parser package.
- This is not a new `ltaw.py` subcommand and does not change the existing
  shared CLI dispatcher.
- Slurm submission, scheduling, and batch-script semantic validation are
  outside this feature.

## Related Documents

- [Current context and decisions](context.md)
- [Standing contract and implementation plan](top_level_plan.md)
- [Workspace index](../../README.md)
