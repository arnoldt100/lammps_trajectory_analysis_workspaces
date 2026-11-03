# Context - LOP-SF-FCC Animation Subcommand

Status snapshot and decision log for the
`workspaces/features/command_line_workspaces/features/lop_sf_fcc_animation_subcommand_workspaces`
feature workspace. It mirrors the scoped subparser package under
`src/lammps_trajectory_analysis_workspaces/cli/`.

## Implementation Status

### Done

- Current scripts-directory launcher and mandatory path options are verified:
  all 41 selected tests passed, including conversion using
  `uv run scripts/ltaw.py lop_sf_fcc_animation --input-file INPUT_FILE
  --output-vtkhdf-file OUTPUT_FILE`. Sample/ParaView checks were not rerun.
- Final combined regression after the script rename and parser validation
  passed all 40 focused CLI/animation tests through `uv run --locked`.
  Both `LTAW_SAMPLE_HDF5` and `LTAW_PVPYTHON` were enabled, covering the
  sample and ParaView reader checks alongside the current CLI behavior.
- Added the subparser builder at
  `src/lammps_trajectory_analysis_workspaces/cli/lop_sf_fcc_animation_subparser.py`.
- Registered the `lop_sf_fcc_animation` command with mandatory
  `--input-file` and `--output-vtkhdf-file`, both parsed as
  `pathlib.Path`. Positional input is rejected.
- Verified option parsing, missing required arguments, positional-input
  rejection, help output, and unchanged handler/path dispatch.
  All 24 focused CLI and animation unit tests passed via `uv run --locked`.
- Bound `LopSfFccAnimation.run_from_cli_args` with
  `set_defaults(func=...)`; shared CLI dispatch invokes `args.func(args)`.
- Added parser and dispatch coverage in
  `tests/command_line/test_cli_arguments.py`.
- Completed Phase 1 reader integration and Phase 2 VTKHDF conversion within
  the animation class, using LTAT's registered builders and converter.
  Generated-file, sample, failure-cleanup, and ParaView reader checks pass;
  all 31 focused tests passed with both opt-in checks enabled.

### Pending

- Interactive rendering and larger-scale behavior remain unverified;
  neither is part of the completed small-input conversion validation.

## Decisions

- Parser validation now requires an existing regular input file and returns
  the supplied `Path` without resolving it. Missing files, directories, and
  broken symlinks fail with argparse exit status 2; symlinks to regular
  files are accepted. Constructor validation remains unchanged and rejects
  inputs removed after parsing. Parsing neither opens HDF5 nor creates output.
  All 37 selected CLI/animation tests passed via `uv run --locked`; opt-in
  sample/ParaView checks were not rerun in this step.
- This feature owns the subparser builder only. The shared command-line
  feature owns the top-level parser and registration; the separate
  `lop_sf_fcc_animation` package owns the callable implementation.
- The command name is exactly `lop_sf_fcc_animation`.
- Current command contract: the HDF5 input is a required `--input-file` `Path`;
  the VTKHDF output is a required `--output-vtkhdf-file` `Path` option.
- Both path options are mandatory; positional input is not supported.
- The entry point is `scripts/ltaw.py`, invoked through `uv run`.
  The user requested the non-conflicting script name, removal of
  `cli/main.py`, and script-only invocation with no installed console command.
- Generic dispatch lives in `ltaw_workspace_parser.run`; the root script
  delegates to it and preserves its return
  contract. All 33 selected CLI/animation tests pass, including script
  conversion from outside the repository. Sample/ParaView tests were not
  rerun in this rename step.
- The subparser binds its handler with `set_defaults(func=...)`, and the main
  program dispatches through `args.func(args)` without a command-name
  conditional.
- The parser does not inspect HDF5 internals or create the output file.
- The LOP-SF-FCC HDF5 input format is produced by the separate project rooted at
  `$LTAT_TOP_LEVEL`, using
  `$LTAT_TOP_LEVEL/src/lammps_trajectory_analysis_tools/lib/lop_sf_fcc/hdf5_writer`.
- Approved Phase 1 construction: use the LTAT package registry with
  `HDF5LopSfFccAnimationSourceBuilderKey` and `file_path` to obtain the source.
  Do not instantiate the concrete reader directly.
- Follow LTAT's existing composition: a builder-created source in Phase 1
  and a builder-created writer value object in Phase 2. A separate reader
  value-object layer is not required; do not add one or use the output
  writer to read input.
- Step 1 (API inspection and architecture approval) is complete. Pause for
  review after each subsequent implementation step.
- Step 2 (dependency declaration and environment validation) is complete:
  `pyproject.toml` declares `lammps-trajectory-analysis-tools` with a
  uv-managed editable source at `../lammps_trajectory_analysis_tools`, and
  `uv.lock` records the resolved dependency graph.
- Verified with `uv run --locked` that `sys.prefix` points to
  `${LTAW_TOP_LEVEL}/.venv`, LTAT imports from the sibling checkout, and its
  registered source builder constructs a closed source without opening an
  input file. All 15 focused animation/CLI tests passed.
- Step 3 is implemented: `_read_hdf5_file` obtains the LTAT source through
  its registered builder, enters its read-only context, and fully consumes
  `frames()` without retaining the trajectory. LTAT validates metadata and
  layout on entry and decoded values during iteration.
- Focused tests verify the builder key/path, full iteration before writing,
  context exit, and propagation of build/open/iteration failures without
  invoking the write stub. All 18 animation/CLI tests passed.
- Real-file integration tests now generate a three-frame HDF5 input through
  LTAT's registered producer writer value-object builder. They verify
  repeated successful reads, rejection of non-HDF5 input, missing datasets,
  and nonfinite values in the final frame. Input hashes remain unchanged,
  read failures do not reach the write stub, and no VTKHDF file is created.
  All 22 focused animation/integration/CLI tests passed.
- The opt-in `test_local_ten_trajectory_sample` passed through LTAT's
  registered source builder and the animation callable. Measured values:
  10 populated frames, 5849 atoms per frame, steps 0 through 9, time step
  2.0 fs, and length units `Angstrom`. Shapes matched the reader contract.
- SHA-256 before and after the sample reads matched:
  `d87928e6d00c515dbf22dcf97f58da724816d6c95f4e1d4bb1dfd1c827085340`.
  No VTKHDF output was created during Phase 1 validation.
- Normal focused suites passed with 22 tests and one explicit sample skip.
- Final Phase 1 validation with the sample enabled passed all 23 focused
  tests through `uv run --locked`. Reader integration and validation are
  complete within the class boundary; independent CLI contract/packaging
  gaps remain tracked separately.
- Phase 2 API inspection is complete. Proposed integration: build LTAT's
  converter through `LopSfFccVtkhdfAnimationConverterBuilderKey`, then invoke
  `convert_hdf5(input_path, output_path)` from `_write_vtkhdf_file`.
  The converter itself builds the source and writer value object through
  the registered builders and owns staged output publication/abort.
- Preserve the pre-read validation followed by a second, streaming read for
  conversion. No in-memory trajectory or open source is retained between
  the two private methods. The second pass is validated independently and
  does not promise a snapshot of the first pass.
- Phase 2 converter delegation is implemented: `_write_vtkhdf_file` builds
  the converter through `LopSfFccVtkhdfAnimationConverterBuilderKey` and calls
  `convert_hdf5` with the exact input and output paths. The private method
  retains its `None` return contract and propagates converter failures.
- Focused tests verify source closure and full iteration before converter
  invocation, builder/path delegation, and build/conversion failures.
  Reader-only integration checks now call `_read_hdf5_file` directly.
  The focused suites passed with 24 tests and one opt-in sample skip;
  Pylance reported no diagnostics for the animation implementation.
- Generated-file VTKHDF integration tests now pass. They verify three
  animation steps, physical times, atom counts, positions, LOP-SF-FCC
  scalars, box arrays, metadata/units, and unchanged input hashes.
- Existing unrelated output and repeated conversion are rejected without
  modifying either input or output. An injected failure after the first
  appended frame propagates and removes staged output without publishing
  a final file.
- Focused suites initially passed with 28 tests and one opt-in sample skip.
- Sample conversion now passes through the full animation callable, writing
  only in pytest's temporary directory. All 10 steps and 5849 atoms per step
  match LTAT's decoded source exactly for positions, LOP-SF-FCC scalars, and
  box arrays. Step numbers, physical times, atom counts, and metadata/units
  also match. Input SHA-256 is unchanged and no staging file remains.
- All 29 focused tests passed with the sample enabled at the sample
  conversion checkpoint.
- ParaView 6.2.0 is available at
  `/home/8nt/sw/paraview/ParaView-6.2.0-MPI-Linux-Python3.12-x86_64`.
  The opt-in reader test invokes its `bin/pvpython` through `uv run --locked`
  without adding dependencies to the project's virtual environment.
- Its VTK HDF reader successfully reads every generated/sample time step
  (3 and 10 respectively), returning PolyData with one vertex per point.
  Positions, LOP-SF-FCC scalars, step numbers, physical times, and box
  arrays match LTAT's decoded source. Input hashes remain unchanged and no
  staging file remains.
- All 31 focused tests pass with the sample and ParaView checks enabled.
  Interactive rendering and larger-scale behavior remain unverified.
  Paused for review after the reader interoperability check.
- Phase 2 HDF5-to-VTKHDF conversion is provided by
  `$LTAT_TOP_LEVEL/src/lammps_trajectory_analysis_tools/lib/lop_sf_fcc_vtkhdf_writer`.
  This project should integrate with the external reader and writer rather
  than reimplement either one.
- Source inspection confirms context-managed read-only opening,
  `metadata`, `layout`, `frame_count`, and lazy `frames()` access. Complete
  frame iteration is necessary to validate decoded values; opening alone
  does not establish a successful full read.
- Use the uv-managed editable dependency on the sibling LTAT project to
  integrate `_read_hdf5_file` without caching all frames. Source cleanup and
  failure propagation must precede any call to the write stub.
- Sample compatibility and the expected 10 populated frames are verified.
- A sample input is available at
  `argon_trajectories/example_lop_sf_fcc_hdf5/ar_box_small.lop_sf_fcc.nm-frames-10.validated.hdf5`.
  It contains only 10 trajectories, so it is a small example for initial
  format/integration checks and should not be treated as representative of
  larger workloads.

## Planned Data Flow

To rerun the opt-in sample verification from the project root:

```sh
LTAW_SAMPLE_HDF5="${LTAW_TOP_LEVEL}/argon_trajectories/example_lop_sf_fcc_hdf5/ar_box_small.lop_sf_fcc.nm-frames-10.validated.hdf5" \
  uv run --locked python -m pytest -s \
  tests/lop_sf_fcc_animation/test_animation_integration.py::test_local_ten_trajectory_sample
```

Without `LTAW_SAMPLE_HDF5` this test skips, keeping normal tests independent
of untracked data. An explicitly configured missing file fails on opening.

To also run the opt-in ParaView reader checks:

```sh
LTAW_PVPYTHON="/home/8nt/sw/paraview/ParaView-6.2.0-MPI-Linux-Python3.12-x86_64/bin/pvpython" \
LTAW_SAMPLE_HDF5="${LTAW_TOP_LEVEL}/argon_trajectories/example_lop_sf_fcc_hdf5/ar_box_small.lop_sf_fcc.nm-frames-10.validated.hdf5" \
  uv run --locked python -m pytest \
  tests/lop_sf_fcc_animation tests/command_line/test_cli_arguments.py
```

Without `LTAW_PVPYTHON`, both ParaView cases skip. Without
`LTAW_SAMPLE_HDF5`, only the generated-input ParaView case runs.
An explicitly configured unavailable executable or a failed reader
subprocess fails the test rather than silently skipping.

```text
top-level CLI parser
        │
        ▼
lop_sf_fcc_animation subparser
        ├─ parse mandatory input/output path options
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
uv run scripts/ltaw.py \
  lop_sf_fcc_animation --input-file INPUT_FILE \
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
