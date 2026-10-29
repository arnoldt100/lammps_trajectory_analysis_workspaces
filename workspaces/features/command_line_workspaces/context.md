# Context - Command-Line Feature

Status snapshot and decision log for the command-line feature. Update this
file whenever the feature's behavior, data flow, or boundaries change.

## Implementation Status

### Done

- The intended task workflow and three-stage pipeline are documented.
- Entry point implemented at
  `scripts/lammps_trajectory_analysis_workspaces.py`.
- Shared parser implemented at
  `src/lammps_trajectory_analysis_workspaces/ltaw_workspace_parser.py`.
- Added `cli_args.py` with the parsed namespace wrapper.
- Added and registered `lop_sf_fcc_animation` with required
  `--input-file` and `--output-vtkhdf-file` path options. This is the current
  implementation; planned usage makes the HDF5 input positional.
- Subparser-specific ICM docs live in
  `workspaces/features/command_line_workspaces/features/lop_sf_fcc_animation_subcommand_workspaces/`;
  this parent workspace covers the shared top-level parser.
- Bound the command to `LopSfFccAnimation.run_from_cli_args` via
  `set_defaults(func=...)`; the main program dispatches with `args.func(args)`.
- Added the callable animation boundary, which validates/stores its paths and
  prints a placeholder conversion message; the planned first phase is
  reading through LTAT's existing HDF5 reader.
- Added CLI and animation contract tests; the focused test suites pass.
- Current gap: input-file existence is checked at callable construction but
  not during argument parsing, so the two-boundary validation requirement is
  not yet fully met.

### Pending

- Add CLI-side input-file existence validation and its parser-level test.
- Change the input from `--input-file` to a required positional `Path`.
- Add a project console-script entry point for
  `lammps_trajectory_analysis_workspaces.py` to support the planned
  `uv run lammps_trajectory_analysis_workspaces.py ...` invocation.
- Phase 1: locate and integrate LTAT's existing HDF5 reader; verify its API,
  input layout, and successful reading of the 10-trajectory sample.
- Phase 2, after phase 1 is complete: integrate LTAT's existing
  `vtkhdf_writer` to write the requested animation file.
- Add phase-specific tests; prioritize HDF5 reader validation and sample-file
  coverage before VTKHDF writer tests.

### Not planned

## Decisions

- Each task has a distinct subcommand.
- `scripts/lammps_trajectory_analysis_workspaces.py` is the main program
  entry point for analysis tasks and animation-plot generation.
- The package parser module owns top-level parser and subcommand construction;
  task-specific logic stays outside the entry-point script.
- `lop_sf_fcc_animation` uses `set_defaults(func=...)` and the main program
  dispatches by invoking the parsed handler with the parsed namespace.
- Planned invocation:
  `uv run lammps_trajectory_analysis_workspaces.py lop_sf_fcc_animation INPUT_FILE --output-vtkhdf-file OUTPUT_VTKHDF_FILE`.
- For the planned contract, `INPUT_FILE` is positional and the command reads
  it as HDF5 LOP-SF-FCC input, then writes the specified VTKHDF output.
- Implement in two phases: first read the HDF5 trajectory through the
  existing LTAT reader and verify this phase; only then implement VTKHDF
  writing through LTAT's `vtkhdf_writer`.
- Reuse LTAT's existing reader/writer packages; keep their domain logic out
  of this project.
- The requested executable name must be exposed as a project console script;
  no such entry point is currently defined in `pyproject.toml`.
- The top-level parser requires a subcommand during normal execution.
- A task generally consists of selecting LAMMPS simulation output files,
  using MDAnalysis to read them and produce HDF5 data, then converting that
  HDF5 data into VTKHDF files for animation.
- Task-specific inputs and options belong to their corresponding subcommand;
  shared parsing and dispatch remain in the CLI feature.
- Feature contract: values consumed by a task are validated at the command
  line and again when its CLI-facing class is constructed. For the current
  animation command, constructor validation exists; parser-level existence
  validation remains a tracked gap.

## Current Data Flow

```text
user invokes task subcommand
        │
        ▼
scripts/lammps_trajectory_analysis_workspaces.py
        │
        ▼
ltaw_workspace_parser.py
        │
        ▼
lop_sf_fcc_animation subparser
        ├─ parse input/output paths and bind func handler
        ▼
LopSfFccAnimation.run_from_cli_args(args)
        │
        ▼
Phase 1: read HDF5 through LTAT's existing reader
        │
        ▼
Phase 2, deferred: write VTKHDF through LTAT's vtkhdf_writer
```

The CLI starts from an existing HDF5 trajectory. Phase 1 is to read it
through LTAT's existing reader and verify the API and data contract using the
10-trajectory example. Phase 2, deferred until phase 1 is complete, is to
write the requested output through LTAT's `vtkhdf_writer`.

## Maintenance Rule

When adding or changing a subcommand or pipeline stage, update its contract
and arguments in `top_level_plan.md`, the implementation boundaries and
dependencies in `README.md`, and this status/data-flow snapshot. Keep tests
aligned with parser validation, task dispatch, stage ordering, and propagation
of stage inputs and outputs.