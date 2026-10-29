# LOP-SF-FCC Animation Subcommand

## Feature Goal

Own the parser builder for the `lop_sf_fcc_animation` command. The subcommand
accepts an existing HDF5 trajectory path and an explicit output VTKHDF path:

```text
lop_sf_fcc_animation \
  --input-file <input-hdf5-file> \
  --output-vtkhdf-file <output-vtkhdf-file>
```

Both options are required. The HDF5 structure and actual conversion behavior
are specified separately; this feature defines the command-line interface
and binds its parsed arguments to the callable animation implementation.

## Responsibilities and Boundaries

This feature owns the subcommand parser builder:

- Production module:
  `src/lammps_trajectory_analysis_workspaces/cli/lop_sf_fcc_animation_subparser.py`
- Public builder:
  `add_lop_sf_fcc_animation_subparser(subparsers)`
- Contract tests:
  `tests/command_line/test_cli_arguments.py`

The builder creates the named subcommand, defines its required path options,
and binds `LopSfFccAnimation.run_from_cli_args` as the `func` handler using
`set_defaults(func=...)`.

The shared top-level parser is owned by the command-line feature at
`src/lammps_trajectory_analysis_workspaces/ltaw_workspace_parser.py`; it
registers this feature's subparser. The executable entry point dispatches
through `args.func(args)`. The callable class and conversion behavior are
owned separately by
`src/lammps_trajectory_analysis_workspaces/lop_sf_fcc_animation/`.

This workspace contains plans and status documentation only. Production code
and tests remain in their centralized source and test locations.

## Dependencies

- Python standard library: `argparse` and `pathlib`.
- CLI handler dependency:
  `LopSfFccAnimation.run_from_cli_args`.
- No HDF5 or VTKHDF libraries are required by the subparser builder.

## Related Documents

- Standing subcommand contract: [top_level_plan.md](top_level_plan.md)
- Current status: [context.md](context.md)
- Shared CLI feature:
  [../../README.md](../../README.md)
