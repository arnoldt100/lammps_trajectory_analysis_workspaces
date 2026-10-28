

# Project Entry Point

The command-line entry point is
`${LTAW_TOP_LEVEL}/scripts/lammps_trajectory_analysis_workspaces.py`. It
drives data-analysis tasks and generation of animation plots. Shared
command-line parsing and subcommand construction belong in the
`lammps_trajectory_analysis_workspaces` package; task-specific analysis and
conversion logic remain with their task implementations. See the command-line
feature plan at
`workspaces/features/command_line_workspaces/top_level_plan.md`.

# Environmental Variables

The environmental variable `LTAW_TOP_LEVEL` defines the root directory of
this Python project.
