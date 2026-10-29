# Top-Level Plan - LOP-SF-FCC Animation Subcommand

This is the canonical standing plan for the
`cli/lop_sf_fcc_animation_subcommand_workspaces` feature. It inherits project
rules from [../../../../top_level_plan.md](../../../../top_level_plan.md) and
the shared CLI contract from [../../top_level_plan.md](../../top_level_plan.md);
this plan must not weaken either.

## Objective

Maintain the parser builder for the distinct `lop_sf_fcc_animation`
subcommand. It accepts an HDF5 trajectory input path and an explicit VTKHDF
animation output path, then associates the parsed namespace with the
callable animation handler.

## Public Command Contract

```text
lop_sf_fcc_animation \
  --input-file <input-hdf5-file> \
  --output-vtkhdf-file <output-vtkhdf-file>
```

- Command name: `lop_sf_fcc_animation`.
- `--input-file`: required, parsed as `pathlib.Path`.
- `--output-vtkhdf-file`: required, parsed as `pathlib.Path`.
- Both values must remain available on the parsed argument namespace.
- The subparser binds `LopSfFccAnimation.run_from_cli_args` with
  `parser.set_defaults(func=...)`.
- The top-level CLI invokes the selected handler as `args.func(args)`.
- Missing required options and unknown options are rejected by argparse.

The input must be an existing regular file before the animation callable
runs. The callable currently enforces that condition at construction.
Parser-level input-file existence validation is a known pending gap; until
implemented, do not claim that the CLI validates existence at both
boundaries.

Do not open or create the output file while parsing. Do not validate HDF5
groups, datasets, attributes, or trajectory layout until that format is
specified.

## Implementation Boundary

```text
src/
  lammps_trajectory_analysis_workspaces/
    cli/
      lop_sf_fcc_animation_subparser.py
    lop_sf_fcc_animation/
      animation.py
tests/
  command_line/
    test_cli_arguments.py
```

- `cli/lop_sf_fcc_animation_subparser.py` owns only subcommand construction,
  option definitions, and handler binding.
- `ltaw_workspace_parser.py` belongs to the shared CLI feature and owns the
  top-level parser and subparser registration.
- `scripts/lammps_trajectory_analysis_workspaces.py` owns process entry and
  generic handler invocation, not task-specific branching or conversion.
- `lop_sf_fcc_animation/animation.py` owns the callable class and any
  eventual HDF5-to-VTKHDF conversion.
- Tests remain centralized under `tests/`; do not put production code in this
  workspace directory.

## Design Rules

- Keep this parser builder focused on CLI syntax and handler binding.
- Do not place HDF5 reading, VTKHDF writing, or animation logic in the
  subparser module.
- Keep input and output paths explicit; do not silently supply defaults.
- Preserve `argparse` error handling for absent required arguments and
  unrecognized options.
- Keep the registered handler compatible with the shared `args.func(args)`
  dispatch convention.
- Record any change to command name, option names, value types, or dispatch
  contract in this plan and in `context.md`.

## Test Plan

1. The shared top-level parser exposes `lop_sf_fcc_animation`.
2. Both required options parse to the corresponding `Path` values.
3. Omitting either required option is rejected.
4. An unknown subcommand option is rejected.
5. The subparser sets `func` to the callable adapter.
6. Dispatch invokes the handler with the parsed namespace and preserves both
   paths unchanged.
7. Invalid input-file values fail through the callable's validation and do
   not produce the placeholder conversion message.
8. Add a parser-side input existence check and corresponding tests to satisfy
   the shared CLI's two-boundary validation contract.
9. Parser tests use temporary files or controlled handlers; they do not
   require production HDF5 trajectory files.

## Non-Goals and Deferred Requirements

- Defining the HDF5 schema or validating its contents.
- Implementing HDF5-to-VTKHDF conversion.
- Selecting LAMMPS outputs or creating the intermediate HDF5 trajectory.
- Deciding output overwrite, directory creation, or intermediate retention
  policy.
- Owning the top-level parser, executable entry point, or animation callable.

## Current Acceptance Status

- The subcommand and required `Path` options are implemented.
- Callable handler binding through `set_defaults(func=...)` and generic
  `args.func(args)` dispatch are implemented.
- Current parser, dispatch, and callable tests pass.
- Parser-side input-file existence validation remains pending.
- Actual conversion and format-specific tests remain pending the HDF5
  structure specification.
