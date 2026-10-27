# Command-Line Feature Workspace

## Feature Goal

Provide a command-line interface with a distinct subcommand for each
simulation-analysis task. A task generally orchestrates this three-stage
pipeline:

1. Select the relevant output files from a LAMMPS molecular dynamics
   simulation.
2. Use MDAnalysis to read those outputs and convert them into an HDF5 data
   file.
3. Convert the HDF5 data into VTKHDF files suitable for animation.

Each subcommand represents one task and supplies the task-specific inputs and
options to the pipeline. The CLI dispatches and coordinates the task; it does
not absorb the task's domain-specific file-conversion logic into the shared
parser.

## Structural Boundaries

The feature owns the CLI entry point, top-level parser, per-task subcommand
builders, and the CLI-level propagation of validated values to the task
implementation. Production code belongs under
`src/lammps_trajectory_analysis_workspaces/`. Tests belong under `tests/` and
cover the CLI contract, dispatch, and pipeline orchestration boundaries.

Exact source and test file paths are to be recorded here when implementation
structure is established. This workspace contains plans and status
documentation only; production code and tests do not belong in this folder.

## External Dependencies

- Python's standard library for command-line parsing and dispatch.
- MDAnalysis for reading relevant LAMMPS outputs and creating HDF5 data.
- HDF5 and VTKHDF writing/conversion capabilities required by the task
  implementations. The concrete libraries and versions are determined by
  those implementations.

## Cross-Feature Dependencies

The CLI dispatches to the task implementations that own simulation parsing
and data conversion. Those task workspaces should document their dependency
on the relevant CLI subcommand once they have feature workspaces. The CLI
workspace should list each consumer/producer relationship as it is
implemented.

## Related Documents

- Standing rules and CLI contract: [top_level_plan.md](top_level_plan.md)
- Current status and decisions: [context.md](context.md)
- Parent workspace rules: [../../top_level_plan.md](../../top_level_plan.md)