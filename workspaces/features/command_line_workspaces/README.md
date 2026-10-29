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

The CLI entry point is
[`scripts/lammps_trajectory_analysis_workspaces.py`](../../../scripts/lammps_trajectory_analysis_workspaces.py).
It invokes `main()` to drive analysis tasks and animation-plot generation.
Shared parser construction is in
[`src/lammps_trajectory_analysis_workspaces/ltaw_workspace_parser.py`](../../../src/lammps_trajectory_analysis_workspaces/ltaw_workspace_parser.py);
it registers the `lop_sf_fcc_animation` subcommand from
[`src/lammps_trajectory_analysis_workspaces/cli/lop_sf_fcc_animation_subparser.py`](../../../src/lammps_trajectory_analysis_workspaces/cli/lop_sf_fcc_animation_subparser.py).
That subparser defines required `--input-file` and `--output-vtkhdf-file`
options and binds the callable handler with `set_defaults(func=...)`.
[`src/lammps_trajectory_analysis_workspaces/cli_args.py`](../../../src/lammps_trajectory_analysis_workspaces/cli_args.py)
wraps the parsed namespace. The entry point dispatches by invoking
`args.func(args)` rather than branching on command names.

The separate callable boundary is
[`src/lammps_trajectory_analysis_workspaces/lop_sf_fcc_animation/animation.py`](../../../src/lammps_trajectory_analysis_workspaces/lop_sf_fcc_animation/animation.py).
It currently validates and stores the paths and prints a placeholder
conversion message; it does not yet read HDF5 or write VTKHDF. Domain
conversion remains task-specific and awaits the HDF5 structure specification.

Tests under `tests/command_line/` and
`tests/lop_sf_fcc_animation/` cover parser behavior, required arguments,
handler binding, dispatch, callable validation, and placeholder invocation.
Input-file existence is currently checked by the callable constructor, not
during argument parsing; adding CLI-side validation remains pending to meet
the feature's two-boundary validation contract. Tests of actual conversion
and HDF5-to-VTKHDF stage behavior remain pending the data-format
specification.

This workspace contains plans and status documentation only; production code
and tests do not belong in this folder.

## External Dependencies

- Python standard library for the implemented command-line parser and path
  handling.
- HDF5 and VTKHDF libraries will be determined when the input structure and
  conversion requirements are specified.

## Cross-Feature Dependencies

The CLI dispatches to the task implementations that own simulation parsing
and data conversion. Those task workspaces should document their dependency
on the relevant CLI subcommand once they have feature workspaces. The CLI
workspace should list each consumer/producer relationship as it is
implemented.

The `lop_sf_fcc_animation` subparser has its own child workspace under
[`features/lop_sf_fcc_animation_subcommand_workspaces/`](features/lop_sf_fcc_animation_subcommand_workspaces/README.md),
while this workspace owns the top-level parser contract.

## Related Documents

- Standing rules and CLI contract: [top_level_plan.md](top_level_plan.md)
- Current status and decisions: [context.md](context.md)
- Parent workspace rules: [../../top_level_plan.md](../../top_level_plan.md)