# File Parser Feature Workspace

## Feature Goal

Generate a Slurm batch file by replacing template placeholders with literal
string values from a JSON file.

This ICM workspace contains planning documents only. Implementation and
tests are not yet created for this feature.

## Structural Boundaries

Planned production files:

- `scripts/create_batch_file.py`: standalone command-line entry point,
  argument parsing, delegation, and user-facing errors.
- `src/lammps_trajectory_analysis_workspaces/file_parser/__init__.py`:
  package boundary.
- `src/lammps_trajectory_analysis_workspaces/file_parser/json_file_parser.py`:
  JSON validation, template substitution, and output-file creation.

Planned tests:

- `tests/file_parser/`: replacement behavior, validation, and file handling.
- `tests/command_line/test_create_batch_file.py`: standalone command behavior.

The existing [`scripts/create_batch_file.py`](../../../scripts/create_batch_file.py)
is a stub, not a working implementation.

## Dependencies and Relationships

- Inherits [project-wide rules](../../top_level_plan.md), including execution
  through `uv run`.
- Uses the Python standard library; no new dependencies are planned.
- The standalone script delegates conversion to the file-parser package.
- This is not a new `ltaw.py` subcommand and does not change the existing
  shared CLI dispatcher.
- Slurm submission, scheduling, and batch-script semantic validation are
  outside this feature.

## Related Documents

- [Current context and decisions](context.md)
- [Standing contract and implementation plan](top_level_plan.md)
- [Workspace index](../../README.md)
