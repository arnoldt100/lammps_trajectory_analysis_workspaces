# File Parser Feature Workspace

## Feature Goal

Generate a Slurm batch file by replacing template placeholders with literal
string values from a JSON file.

This ICM workspace tracks the plan and implementation status. Stage 1,
Phase 1 adds the shared `FileParserOptions` dataclass and five passing
contract tests; it is pending user review. Parsing and conversion are not
yet implemented.

## Implementation Stages

1. Add the shared options dataclass and implement and test a standalone
   parsing function that returns it.
2. Implement the JSON file module and pass the returned dataclass to it,
   then verify conversion and command-line error handling.

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
  JSON validation, template substitution, and output-file creation.

Planned tests:

- `tests/file_parser/test_file_parser_options.py`: shared options contract
  (implemented in Stage 1, Phase 1).
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
