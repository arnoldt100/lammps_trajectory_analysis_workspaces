# LOP-SF-FCC Animation Subcommand

## Feature Goal

Own the parser builder for the `lop_sf_fcc_animation` command. The subcommand
accepts an existing HDF5 trajectory path and an explicit output VTKHDF path:

```text
uv run lammps_trajectory_analysis_workspaces.py \
  lop_sf_fcc_animation <input-hdf5-file> \
  --output-vtkhdf-file <output-vtkhdf-file>
```

The HDF5 input is positional and the VTKHDF output option is required.
Implementation is planned in two phases:

1. Read the HDF5 LOP-SF-FCC trajectory using the existing reader package in
   the project at `$LTAT_TOP_LEVEL`.
2. Write the requested VTKHDF animation using that project's existing
   `vtkhdf_writer` package.

The exact reader/writer APIs, HDF5 layout, and dependency integration still
need inspection. This project should orchestrate those packages rather than
duplicate their HDF5-reading or VTKHDF-writing logic.

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
The HDF5 input format is produced by
`$LTAT_TOP_LEVEL/SRC/lammps_trajectory_analysis_tools/lib/lop_sf_fcc/hdf5_writer`.
The external project's existing HDF5 reader package (exact module/API to be
identified during phase 1) reads that trajectory. Conversion from the HDF5
LOP-SF-FCC file to VTKHDF is provided by
`$LTAT_TOP_LEVEL/SRC/lammps_trajectory_analysis_tools/lib/lop_sf_fcc/vtkhdf_writer`.
The local callable should integrate with these packages rather than
reimplement their functionality.

The requested `uv run lammps_trajectory_analysis_workspaces.py ...` form
requires a project console-script entry point with this executable name.
Adding that packaging entry point is part of the planned CLI work; the
current `pyproject.toml` does not yet declare it.

This workspace contains plans and status documentation only. Production code
and tests remain in their centralized source and test locations.

## Dependencies

- Python standard library: `argparse` and `pathlib`.
- CLI handler dependency:
  `LopSfFccAnimation.run_from_cli_args`.
- External project dependency for LOP-SF-FCC HDF5 reading and VTKHDF
  conversion: the reader package to be identified in phase 1 and
  `vtkhdf_writer` under
  `$LTAT_TOP_LEVEL/SRC/lammps_trajectory_analysis_tools/lib/lop_sf_fcc/`.
- No HDF5 or VTKHDF libraries are required by the subparser builder itself.

## Related Documents

- Standing subcommand contract: [top_level_plan.md](top_level_plan.md)
- Current status: [context.md](context.md)
- Shared CLI feature:
  [../../README.md](../../README.md)
