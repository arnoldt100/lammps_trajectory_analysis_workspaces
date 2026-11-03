# LOP-SF-FCC Animation Subcommand

## Feature Goal

Own the parser builder for the `lop_sf_fcc_animation` command. The subcommand
accepts an existing HDF5 trajectory path and an explicit output VTKHDF path:

```text
uv run scripts/ltaw.py \
  lop_sf_fcc_animation --input-file <input-hdf5-file> \
  --output-vtkhdf-file <output-vtkhdf-file>
```

Both `--input-file` and `--output-vtkhdf-file` are mandatory.
Positional input is rejected. Invocation is script-only from the project root;
no console-script entry point is declared.
Both argument parsing and callable construction require an existing regular
input file. Argparse rejects missing files, directories, and broken symlinks;
symlinks to regular files are accepted without resolving the supplied path.
HDF5 schema/content validation remains with LTAT.
Conversion within the animation class is complete in two phases:

1. Read the HDF5 LOP-SF-FCC trajectory using the existing reader package in
   the project at `$LTAT_TOP_LEVEL`.
2. Write the requested VTKHDF animation using that project's existing
   `vtkhdf_writer` package.

LTAT exports `HDF5LopSfFccAnimationSource` for read-only schema validation
and lazy frame decoding. The approved construction path follows LTAT's
existing architecture: obtain this source through its registered source
builder in Phase 1, and use the registered writer value-object builder in
Phase 2. No new reader value-object layer is required. This project should
orchestrate LTAT's packages rather than duplicate their reading or writing
logic.

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
`$LTAT_TOP_LEVEL/src/lammps_trajectory_analysis_tools/lib/lop_sf_fcc/hdf5_writer`.
The reader is `HDF5LopSfFccAnimationSource` in the canonical public package
`lammps_trajectory_analysis_tools.lib.lop_sf_fcc_vtkhdf_writer`. That package
also owns conversion to VTKHDF and is located at
`$LTAT_TOP_LEVEL/src/lammps_trajectory_analysis_tools/lib/lop_sf_fcc_vtkhdf_writer/`.
The local callable should integrate with these packages rather than
reimplement their functionality.

The invocation is `uv run scripts/ltaw.py ...`. The script's non-conflicting
name avoids shadowing the package. It delegates to `ltaw_workspace_parser.run`; the user
requested removal of `cli/main.py` and chose no installed console command.
Script conversion from outside the repository is tested.

This workspace contains plans and status documentation only. Production code
and tests remain in their centralized source and test locations.

## Dependencies

- Python standard library: `argparse` and `pathlib`.
- CLI handler dependency:
  `LopSfFccAnimation.run_from_cli_args`.
- Declared uv-managed editable dependency: `lammps-trajectory-analysis-tools`
  from the sibling LTAT checkout, using its canonical
  `lib.lop_sf_fcc_vtkhdf_writer` reader/writer exports.
- No HDF5 or VTKHDF libraries are required by the subparser builder itself.

## Related Documents

- Standing subcommand contract: [top_level_plan.md](top_level_plan.md)
- Current status: [context.md](context.md)
- Shared CLI feature:
  [../../README.md](../../README.md)
