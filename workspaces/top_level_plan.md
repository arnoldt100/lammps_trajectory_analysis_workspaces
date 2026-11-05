

# Project Entry Point

The command-line entry point is
`${LTAW_TOP_LEVEL}/scripts/ltaw.py`. It
drives data-analysis tasks and generation of animation plots. Shared
command-line parsing and subcommand construction belong in the
`lammps_trajectory_analysis_workspaces` package; task-specific analysis and
conversion logic remain with their task implementations. See the command-line
feature plan at
`workspaces/features/command_line_workspaces/top_level_plan.md`.

The separately planned `${LTAW_TOP_LEVEL}/scripts/create_batch_file.py`
entry point generates Slurm batch files from a template and JSON
replacement instructions. It delegates conversion to the `file_parser`
package rather than using the analysis CLI dispatcher. See the
[file-parser feature plan](features/file_parser_workspaces/top_level_plan.md).

# Environmental Variables

The environmental variable `LTAW_TOP_LEVEL` defines the root directory of
this Python project.

# Python Environment and Commands

The project's Python virtual environment is located at
`${LTAW_TOP_LEVEL}/.venv`. Run Python commands and scripts through `uv run`
so they use the project's managed environment (for example,
`uv run scripts/ltaw.py --help`).
