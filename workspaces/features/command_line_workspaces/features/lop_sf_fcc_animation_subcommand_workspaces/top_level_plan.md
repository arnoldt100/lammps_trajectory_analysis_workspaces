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
callable animation handler. Implement the functionality in two phases:
first read the HDF5 trajectory using the existing reader package in the
project at `$LTAT_TOP_LEVEL`; after that phase is verified, write the
animation using that project's `vtkhdf_writer` package.

## Public Command Contract

```text
uv run lammps_trajectory_analysis_workspaces.py \
  lop_sf_fcc_animation <input-hdf5-file> \
  --output-vtkhdf-file <output-vtkhdf-file>
```

- Command name: `lop_sf_fcc_animation`.
- The HDF5 input path is a required positional argument parsed as
  `pathlib.Path`.
- `--output-vtkhdf-file`: required, parsed as `pathlib.Path`.
- Both values must remain available on the parsed argument namespace.
- The completed command must read the HDF5 LOP-SF-FCC trajectory and write
  the requested VTKHDF animation file, using existing packages in
  `$LTAT_TOP_LEVEL` for both phases.
- Invoke through `uv run` using the executable name
  `lammps_trajectory_analysis_workspaces.py`.
- The subparser binds `LopSfFccAnimation.run_from_cli_args` with
  `parser.set_defaults(func=...)`.
- The top-level CLI invokes the selected handler as `args.func(args)`.
- Missing required options and unknown options are rejected by argparse.

The current parser still takes the input through `--input-file`, and
`pyproject.toml` does not yet expose the requested executable as a
console-script entry point. These are implementation gaps against the
planned command contract.

The input must be an existing regular file before the animation callable
runs. The callable currently enforces that condition at construction.
Parser-level input-file existence validation is a known pending gap; until
implemented, do not claim that the CLI validates existence at both
boundaries.

Do not open or create the output file while parsing. Establish the HDF5
layout and reader API in phase 1 by inspecting the external reader and sample
file.

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
- `lop_sf_fcc_animation/animation.py` owns the callable class and
  orchestration of the two external-package phases.
- `$LTAT_TOP_LEVEL/SRC/lammps_trajectory_analysis_tools/lib/lop_sf_fcc/hdf5_writer`
  produces the input HDF5 LOP-SF-FCC file format.
- Phase 1 must use the existing LTAT package for reading the HDF5 trajectory;
  identify its exact path, public API, and data contract before coding.
- `$LTAT_TOP_LEVEL/SRC/lammps_trajectory_analysis_tools/lib/lop_sf_fcc/vtkhdf_writer`
  provides phase 2 conversion from the HDF5 trajectory to VTKHDF.
- Reuse the external reader and writer; do not duplicate their
  implementations in this project.
- A small example input is available at
  [`argon_trajectories/example_lop_sf_fcc_hdf5/ar_box_small.lop_sf_fcc.nm-frames-10.validated.hdf5`](../../../../../argon_trajectories/example_lop_sf_fcc_hdf5/ar_box_small.lop_sf_fcc.nm-frames-10.validated.hdf5);
  it contains 10 trajectories and can support initial integration checks.
  It does not establish performance or behavior for larger trajectory sets.
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

## Two-Phase Implementation Plan

### Phase 1: Read the HDF5 LOP-SF-FCC Trajectory

Phase 1 is the immediate implementation focus. Do not implement phase 2
until the phase-1 reader integration and data contract are verified.

1. Inspect `$LTAT_TOP_LEVEL` to locate and understand its existing HDF5
   reader, public API, expected input layout, and dependency/import mechanism.
2. Use the 10-trajectory example file to verify that the external reader can
   open and read the expected trajectory.
3. Implement a thin local integration boundary that accepts the input path
   and delegates reading to LTAT; keep HDF5 parsing logic in that project.
4. Test input validation, successful reading, expected data access, and
   reader failure propagation. Prefer the sample HDF5 file for integration
   coverage and controlled substitutes for focused unit tests.
5. Consider phase 1 complete only when the reader API/data contract and
   successful sample-file read are verified. Do not begin VTKHDF writing
   during this phase.

### Phase 2: Write the VTKHDF Animation

1. Inspect the external `vtkhdf_writer` API and determine how it consumes
   the HDF5 file or phase-1 read result.
2. Integrate the writer to create the requested output file from the input
   trajectory; do not reimplement VTKHDF serialization locally.
3. Test output path propagation, successful file creation, and writer error
   propagation. Use the 10-trajectory sample for initial end-to-end coverage.
4. Verify any scale-dependent behavior separately with a larger input.

## Test Plan

1. The shared top-level parser exposes `lop_sf_fcc_animation`.
2. The positional input and required output option parse to the corresponding
   `Path` values.
3. Omitting the positional input or output option is rejected.
4. An unknown subcommand option is rejected.
5. The subparser sets `func` to the callable adapter.
6. Dispatch invokes the handler with the parsed namespace and preserves both
   paths unchanged.
7. `uv run lammps_trajectory_analysis_workspaces.py` resolves to the CLI
   through a declared project console-script entry point.
8. Invalid input-file values fail through the callable's validation and do
   not produce the placeholder conversion message.
9. Add a parser-side input existence check and corresponding tests to satisfy
   the shared CLI's two-boundary validation contract.
10. Phase 1 reads the sample HDF5 trajectory through the external LTAT
   reader and surfaces failures.
11. Phase 2 invokes the external `vtkhdf_writer` and writes the requested
   output path.
12. Parser tests use temporary files or controlled handlers; they do not
   require production HDF5 trajectory files.

## Non-Goals and Deferred Requirements

- Reimplementing the HDF5 reader or HDF5-to-VTKHDF writer owned by the
  external LOP-SF-FCC project.
- Defining a separate HDF5 schema; use the format produced by the external
  `hdf5_writer` package.
- Selecting LAMMPS outputs or creating the intermediate HDF5 trajectory.
- Deciding output overwrite, directory creation, or intermediate retention
  policy.
- Owning the top-level parser, executable entry point, or animation callable.

## Current Acceptance Status

- The subcommand is implemented, but currently accepts `--input-file`
  rather than the planned positional input.
- The requested `uv run` console-script entry point is not yet declared.
- Callable handler binding through `set_defaults(func=...)` and generic
  `args.func(args)` dispatch are implemented.
- Current parser, dispatch, and callable tests pass.
- Parser-side input-file existence validation remains pending.
- Phase 1 HDF5 reader API, dependency integration, and sample-file read
  verification remain pending.
- Phase 2 VTKHDF writing is deferred until phase 1 is complete.
