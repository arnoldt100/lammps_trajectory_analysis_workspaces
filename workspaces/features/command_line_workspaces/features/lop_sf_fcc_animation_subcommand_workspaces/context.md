# Context - LOP-SF-FCC Animation Subcommand

Status snapshot and decision log for the
`workspaces/features/command_line_workspaces/features/lop_sf_fcc_animation_subcommand_workspaces`
feature workspace. It mirrors the scoped subparser package under
`src/lammps_trajectory_analysis_workspaces/cli/`.

## Implementation Status

### Done

- Added the subparser builder at
  `src/lammps_trajectory_analysis_workspaces/cli/lop_sf_fcc_animation_subparser.py`.
- Registered the `lop_sf_fcc_animation` command with required
  `--input-file` and `--output-vtkhdf-file` options, both parsed as
  `pathlib.Path`. This is the current implementation; it differs from the
  planned positional input contract below.
- Bound `LopSfFccAnimation.run_from_cli_args` with
  `set_defaults(func=...)`; shared CLI dispatch invokes `args.func(args)`.
- Added parser and dispatch coverage in
  `tests/command_line/test_cli_arguments.py`.

### Pending

- Change the planned invocation to
  `uv run lammps_trajectory_analysis_workspaces.py lop_sf_fcc_animation INPUT_FILE --output-vtkhdf-file OUTPUT_VTKHDF_FILE`,
  with `INPUT_FILE` as a required positional `Path`.
- Add a project console-script entry point named
  `lammps_trajectory_analysis_workspaces.py` so the requested `uv run`
  invocation resolves; `pyproject.toml` currently does not declare one.
- Validate input-file existence during argument processing, in addition to
  the existing callable-construction check.
- Implement this functionality in two phases:
  1. Read the HDF5 LOP-SF-FCC trajectory using the existing reader package
     in `$LTAT_TOP_LEVEL`; identify and verify its exact package/API and data
     contract.
  2. After phase 1 is complete and verified, write the requested VTKHDF
     animation using the external `vtkhdf_writer` package.
- Keep phase 2 deferred until phase 1 is complete; do not duplicate the
  external project's HDF5 reader or VTKHDF writer.
- Add phase-specific tests, starting with HDF5 reading using the available
  10-trajectory sample, then VTKHDF writing.

## Decisions

- This feature owns the subparser builder only. The shared command-line
  feature owns the top-level parser and registration; the separate
  `lop_sf_fcc_animation` package owns the callable implementation.
- The command name is exactly `lop_sf_fcc_animation`.
- Planned command contract: the HDF5 input is a required positional `Path`;
  the VTKHDF output is a required `--output-vtkhdf-file` `Path` option.
- Current implementation still accepts the input as `--input-file`; update
  the parser and tests to match the planned positional input contract.
- The target executable name is `lammps_trajectory_analysis_workspaces.py`
  and it is invoked through `uv run`.
- The subparser binds its handler with `set_defaults(func=...)`, and the main
  program dispatches through `args.func(args)` without a command-name
  conditional.
- The parser does not inspect HDF5 internals or create the output file.
- The LOP-SF-FCC HDF5 input format is produced by the separate project rooted at
  `$LTAT_TOP_LEVEL`, using
  `$LTAT_TOP_LEVEL/SRC/lammps_trajectory_analysis_tools/lib/lop_sf_fcc/hdf5_writer`.
- Phase 1 reads this file through an existing HDF5 reader package in the
  external project; identify its exact package and API before implementation.
- Phase 2 HDF5-to-VTKHDF conversion is provided by
  `$LTAT_TOP_LEVEL/SRC/lammps_trajectory_analysis_tools/lib/lop_sf_fcc/vtkhdf_writer`.
  This project should integrate with the external reader and writer rather
  than reimplement either one.
- The reader/writer interfaces, expected HDF5 layout, and dependency/import
  mechanism have not yet been inspected or established.
- A sample input is available at
  `argon_trajectories/example_lop_sf_fcc_hdf5/ar_box_small.lop_sf_fcc.nm-frames-10.validated.hdf5`.
  It contains only 10 trajectories, so it is a small example for initial
  format/integration checks and should not be treated as representative of
  larger workloads.

## Current Data Flow

```text
top-level CLI parser
        │
        ▼
lop_sf_fcc_animation subparser
        ├─ parse required positional input and output option
        └─ attach LopSfFccAnimation.run_from_cli_args as func
        │
        ▼
args.func(args)
        │
        ▼
phase 1: callable reads HDF5 through the external LTAT reader
        │
        ▼
phase 2: callable writes VTKHDF through external vtkhdf_writer
```

Target user invocation:

```text
uv run lammps_trajectory_analysis_workspaces.py \
  lop_sf_fcc_animation INPUT_FILE \
  --output-vtkhdf-file OUTPUT_VTKHDF_FILE
```

The completed command must read `INPUT_FILE` as an HDF5 LOP-SF-FCC
trajectory and write `OUTPUT_VTKHDF_FILE` through the external
`vtkhdf_writer` package. Implement and verify the read phase before beginning
the write phase.

Planned two-phase processing boundary:

```text
Phase 1: HDF5 LOP-SF-FCC file
        │
        ▼
external LTAT HDF5 reader
        │
        ▼
read trajectory data
        │
        ▼
Phase 2: external vtkhdf_writer package
        │
        ▼
requested VTKHDF output file
```

Complete and test phase 1 before starting phase 2.

## Maintenance Rule

When the command name, option contract, handler binding, or validation
behavior changes, update this context and `top_level_plan.md`. Keep the
shared command-line feature documentation aligned with the subparser's public
contract.
