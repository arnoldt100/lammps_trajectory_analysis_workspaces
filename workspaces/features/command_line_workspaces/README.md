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
[`scripts/ltaw.py`](../../../scripts/ltaw.py), invoked through
`uv run scripts/ltaw.py` from the project root. It delegates to the package's
`ltaw_workspace_parser.run`; there is no
installed console-script entry point.
It invokes `main()` to drive analysis tasks and animation-plot generation.
Shared parser construction is in
[`src/lammps_trajectory_analysis_workspaces/ltaw_workspace_parser.py`](../../../src/lammps_trajectory_analysis_workspaces/ltaw_workspace_parser.py);
it registers the `lop_sf_fcc_animation` subcommand from
[`src/lammps_trajectory_analysis_workspaces/cli/lop_sf_fcc_animation_subparser.py`](../../../src/lammps_trajectory_analysis_workspaces/cli/lop_sf_fcc_animation_subparser.py).
The `lop_sf_fcc_animation` invocation requires both `--input-file` and
`--output-vtkhdf-file`; it binds the callable handler with
`set_defaults(func=...)`. Positional input is not accepted.
[`src/lammps_trajectory_analysis_workspaces/cli/cli_args.py`](../../../src/lammps_trajectory_analysis_workspaces/cli/cli_args.py)
wraps the parsed namespace. The entry point dispatches by invoking
`args.func(args)` rather than branching on command names.

The separate callable boundary is
[`src/lammps_trajectory_analysis_workspaces/lop_sf_fcc_animation/animation.py`](../../../src/lammps_trajectory_analysis_workspaces/lop_sf_fcc_animation/animation.py).
It validates and stores the paths, reads through LTAT's registered source
builder with context-managed frame iteration, then delegates writing to
LTAT's registered converter and its writer value-object construction path.
Generated-file output integration tests and 10-trajectory sample conversion
pass. Output contents are checked with h5py and ParaView 6.2.0's VTK HDF
reader at every time step; interactive rendering remains unverified.
Implementation is complete within the animation class in two phases, reusing the existing
packages in `$LTAT_TOP_LEVEL`: first read the HDF5 trajectory through LTAT's
reader, then write the VTKHDF animation through its `vtkhdf_writer`.
The parser and callable constructor both require an existing regular input file.
Do not duplicate external reader or writer logic.

The target invocation is
`uv run scripts/ltaw.py lop_sf_fcc_animation --input-file INPUT_FILE --output-vtkhdf-file OUTPUT_VTKHDF_FILE`.
The script was renamed to avoid shadowing the package. The user chose
script-only invocation rather than an installed console command.

Tests under `tests/command_line/` and
`tests/lop_sf_fcc_animation/` cover parser behavior, required arguments,
handler binding, dispatch, both input-validation boundaries, and conversion.
Missing files, directories, and broken symlinks are rejected by argparse
with exit status 2; symlinks to regular files are accepted without resolving
the supplied path. Constructor validation remains active if the input is
removed after parsing. HDF5 contents are validated by LTAT, not the parser.
All 37 selected CLI/animation tests pass after parser validation was added;
the opt-in sample and ParaView checks were not rerun in this step.

This workspace contains plans and status documentation only; production code
and tests do not belong in this folder.

## External Dependencies

- Python standard library for the implemented command-line parser and path
  handling.
- LTAT's canonical `lammps_trajectory_analysis_tools.lib.lop_sf_fcc_vtkhdf_writer`
  package exports `HDF5LopSfFccAnimationSource` for phase 1 and the converter
  for phase 2. The approved approach uses the registered source builder for
  reading and the writer value-object builder for output, matching LTAT's
  existing architecture. Editable dependency integration and project-environment
  import/builder checks and actual 10-trajectory sample reading are verified.

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