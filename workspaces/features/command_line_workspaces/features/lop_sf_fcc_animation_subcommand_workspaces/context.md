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
  `pathlib.Path`.
- Bound `LopSfFccAnimation.run_from_cli_args` with
  `set_defaults(func=...)`; shared CLI dispatch invokes `args.func(args)`.
- Added parser and dispatch coverage in
  `tests/command_line/test_cli_arguments.py`.

### Pending

- Validate input-file existence during argument processing, in addition to
  the existing callable-construction check.
- Implement actual HDF5-to-VTKHDF conversion after the HDF5 structure and
  conversion requirements are specified. The callable currently prints the
  placeholder text `converting HDF5 to VTKHDF`.
- Add format-specific conversion tests after the data format is established.

## Decisions

- This feature owns the subparser builder only. The shared command-line
  feature owns the top-level parser and registration; the separate
  `lop_sf_fcc_animation` package owns the callable implementation.
- The command name is exactly `lop_sf_fcc_animation`.
- The input and output are explicit required `Path` arguments.
- The subparser binds its handler with `set_defaults(func=...)`, and the main
  program dispatches through `args.func(args)` without a command-name
  conditional.
- The parser does not inspect HDF5 internals or create the output file.

## Current Data Flow

```text
top-level CLI parser
        │
        ▼
lop_sf_fcc_animation subparser
        ├─ parse required input/output paths
        └─ attach LopSfFccAnimation.run_from_cli_args as func
        │
        ▼
args.func(args)
        │
        ▼
callable validates input and prints placeholder message
```

## Maintenance Rule

When the command name, option contract, handler binding, or validation
behavior changes, update this context and `top_level_plan.md`. Keep the
shared command-line feature documentation aligned with the subparser's public
contract.
