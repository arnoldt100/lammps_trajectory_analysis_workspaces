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
uv run ltaw.py \
  lop_sf_fcc_animation --input-file <input-hdf5-file> \
  --output-vtkhdf-file <output-vtkhdf-file>
```

- Command name: `lop_sf_fcc_animation`.
- The HDF5 input path is a required `--input-file` option parsed as
  `pathlib.Path`.
- `--output-vtkhdf-file`: required, parsed as `pathlib.Path`.
- Both values must remain available on the parsed argument namespace.
- The completed command must read the HDF5 LOP-SF-FCC trajectory and write
  the requested VTKHDF animation file, using existing packages in
  `$LTAT_TOP_LEVEL` for both phases.
- Invoke through `uv run ltaw.py`.
- The subparser binds `LopSfFccAnimation.run_from_cli_args` with
  `parser.set_defaults(func=...)`.
- The top-level CLI invokes the selected handler as `args.func(args)`.
- Missing required options and unknown options are rejected by argparse.

The parser requires both path options; positional input is rejected.
The user chose root-script invocation through
`ltaw.py`, avoiding the package-name collision. No console script
is declared in `pyproject.toml`.

The input must be an existing regular file during parsing and again at
callable construction. Missing paths, directories, and broken symlinks
produce argparse errors with exit status 2. Symlinks to regular files are
accepted, preserving the supplied path. Constructor checks remain active
if the input disappears after parsing. The parser does not inspect HDF5.

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
- `ltaw.py` owns process entry and
  generic handler invocation, not task-specific branching or conversion.
- `lop_sf_fcc_animation/animation.py` owns the callable class and
  orchestration of the two external-package phases.
- `$LTAT_TOP_LEVEL/src/lammps_trajectory_analysis_tools/lib/lop_sf_fcc/hdf5_writer`
  produces the input HDF5 LOP-SF-FCC file format.
- Phase 1 uses LTAT's exported `HDF5LopSfFccAnimationSource`, as detailed
  below.
- `$LTAT_TOP_LEVEL/src/lammps_trajectory_analysis_tools/lib/lop_sf_fcc_vtkhdf_writer`
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

Completed: reader integration and the data contract were verified before
Phase 2 implementation began.

#### Verified LTAT Reader

Source inspection identifies the canonical public package as
`lammps_trajectory_analysis_tools.lib.lop_sf_fcc_vtkhdf_writer`, located at
`$LTAT_TOP_LEVEL/src/lammps_trajectory_analysis_tools/lib/lop_sf_fcc_vtkhdf_writer/`.
Use lowercase `src`; the previously recorded uppercase `SRC` and nested
`lop_sf_fcc/vtkhdf_writer` paths do not identify the current implementation.

The previously identified low-level reading API is
`HDF5LopSfFccAnimationSource`, constructed through
`lop_sf_fcc_vtkhdf_animation_writer_factory.build` with
`HDF5LopSfFccAnimationSourceBuilderKey` and `file_path=input_file`. The builder
returns a closed source implementing `LopSfFccVtkhdfAnimationSourceInterface`.
This is a concrete resource adapter, not a reader value object. Using its
registered builder is the approved Phase 1 construction path, consistent
with LTAT's existing converter.

- `with source:` opens the file read-only, validates the producer schema, and
  closes it on exit, including when frame iteration raises.
- While open, `metadata`, `layout`, and `frame_count` expose the validated
  source description and number of populated trajectory groups.
- `frames()` lazily yields `LopSfFccVtkhdfAnimationFrame` objects in group
  order. Each frame supplies `step_number`, `positions`,
  `lop_sf_fcc_values`, `box_lengths`, and `box_angles`.
- `open()` validates groups, shapes, dtypes, units, and increasing step
  numbers. Frame iteration additionally validates decoded values, including
  finite arrays and valid box geometry. Opening alone is not a full read.
- The reader currently accepts at most one frame per trajectory group,
  permits trailing empty groups, and rejects interior gaps. Verify the
  sample against this contract rather than assuming compatibility.
- LTAT raises `DataWriterTargetError` for opening/decoding failures,
  `DataWriterConfigurationError` for incompatible data, and
  `DataWriterLifecycleError` for use outside the open lifecycle.

These are source-verified API facts, not a claim that the local example has
already been read successfully.

#### Approved Builder and Value-Semantics Boundary

Follow LTAT's existing composition rather than introduce a new reader
value-object layer:

- Phase 1 constructs `HDF5LopSfFccAnimationSource` through the package
  registry using `HDF5LopSfFccAnimationSourceBuilderKey` and `file_path`.
  Application code uses the source's public lifecycle and frame interface;
  it does not instantiate the concrete source directly.
- Phase 2 constructs the output writer value object through
  `LopSfFccVtkhdfAnimationWriterValueObjectBuilderKey`, either through LTAT's
  converter or its registered builder. Preserve LTAT's state/behavior
  composition and resource exclusion from value identity.
- The source and writer have distinct roles. Do not use the writer value
  object to read input or duplicate LTAT's architecture locally.

The user approved this existing LTAT architecture after reviewing the package
registry. A separate reader value object is no longer a prerequisite.
Pause after each implementation step for review and approval before starting
the next step.

#### Implementation Sequence

1. Completed: inspect and approve LTAT's source-builder/public-reader
   interface for Phase 1 and writer value-object builder for Phase 2.
2. Completed: declare `lammps-trajectory-analysis-tools` as a project dependency and
   configure a uv-managed editable local source for the sibling LTAT
   checkout. Regenerate the lockfile with uv and verify imports through
   `uv run` using `${LTAW_TOP_LEVEL}/.venv`. Do not modify LTAT or add
   runtime `sys.path`/`PYTHONPATH` workarounds. The declared LTAT dependency
   currently brings its full dependency set; do not invent a reader-only
   extra that LTAT does not publish.
3. Implemented: replace `_read_hdf5_file`'s debug body with source construction through
   LTAT's registry using `HDF5LopSfFccAnimationSourceBuilderKey`. Use its
   public lifecycle to read and close the input, without accessing private
   state or constructing the concrete reader. Keep the method's `None`
   return contract for phase 1. Let LTAT validate metadata/layout on open
   and consume every frame while the reader is open;
   do not return a lazy iterator backed by a closed file.
4. Keep frame processing streaming: do not accumulate a list of frames or
   copy arrays into a local trajectory model. The phase-1 milestone is
   reading/validating the complete input, not caching data for phase 2.
   Leave `_write_vtkhdf_file` as the existing debug-only skeleton, with no
   output creation and no claim that conversion completed.
5. Preserve read-before-write orchestration in `__call__`. If reader
   construction, opening, or iteration fails, propagate the exception and
   do not invoke the write stub. Always close an opened source.
6. Add focused unit coverage using a controlled source with the
   same public interface: correct source builder key/path, no direct
   concrete-reader construction, metadata/layout access, complete
   ordered iteration, context cleanup on success/failure, error propagation,
   repeated calls, and no writer invocation after a read failure.
7. Completed: generate small valid/invalid integration inputs using LTAT's existing
   producer writer in temporary directories. Test a valid multi-group file,
   a non-HDF5 file, incompatible schema, and invalid decoded frame values.
   Leave schema parsing/validation in LTAT; tests should exercise delegation,
   not implement a second parser.
8. Completed: add an explicit local-sample integration check for
   `argon_trajectories/example_lop_sf_fcc_hdf5/ar_box_small.lop_sf_fcc.nm-frames-10.validated.hdf5`.
   Read the file without modification, assert the reported frame count and
   number yielded are both 10, and verify increasing steps, positions shaped
   `(number_of_atoms, 3)`, one LOP-SF-FCC value per atom, and three-element box
   arrays. Record actual metadata and dimensions only after measurement.
   Because this sample is untracked, keep normal tests independent of its
   presence; the explicit sample check must fail clearly if it is absent.
9. Completed: run targeted animation/CLI tests through `uv run`, verify the sample read,
   and confirm the input is unchanged and no VTKHDF file was created. Update
   context with measured results before marking phase 1 complete.

CLI option and executable-entry-point changes remain separately
tracked work; they are not prerequisites for testing `_read_hdf5_file`
through the existing class boundary. Do not add a new read-only CLI mode or
change the output-option contract as part of this phase.

Phase 2 will reuse LTAT's existing converter/writer contract. Its
`LopSfFccVtkhdfAnimationConverter.convert(source, target_path)` owns opening
and closing a supplied source, and `convert_hdf5` builds one from a path.
Do not pass a closed frame generator to it or assume it needs a locally
materialized trajectory; settle final handoff during phase-2 planning.

### Phase 2: Write the VTKHDF Animation

1. Completed: inspect LTAT's converter, writer value-object lifecycle, and
   integration tests. The integration below was approved and implemented.
2. Implemented: replace `_write_vtkhdf_file`'s debug body with construction through
   `LopSfFccVtkhdfAnimationConverterBuilderKey` on the existing factory, then
   call `convert_hdf5(self._input_file, self._output_vtkhdf_file)`. Keep
   `__call__`'s read-then-write order and both methods' `None` return contract.
   The converter builds the source and output writer value object through
   their registered builders. Do not duplicate its frame-copying loop.
3. Keep the two-pass behavior explicit: Phase 1 fully validates the input
   and closes it; Phase 2 reopens it and streams frames into the writer.
   No trajectory cache, retained live handle, or closed generator is passed
   between methods. This costs a second read but preserves bounded memory,
   the approved private-method boundaries, and LTAT's existing lifecycle.
   If input changes between passes, LTAT validates it again during writing;
   this is not a guarantee of snapshot consistency between the two passes.
4. Preserve LTAT's output policy: creation refuses an existing target,
   staged output is published on successful writer context exit, and a
   frame/write failure aborts staged creation. Do not add overwrite,
   directory-creation, append, or alternate dtype policies in this step.
5. Completed: add focused tests for the converter builder key, exact input/output path
   propagation, read-before-write order, converter failure propagation,
   and lack of writer invocation after pre-read failure.
6. Completed: update generated-file integration tests to verify actual output:
   temporal step count and values, atom counts, positions, LOP-SF-FCC
   scalars, box arrays, metadata/units, and unchanged input. Test refusal
   of existing output without modifying it, repeat invocation failure
   rather than overwrite, and output cleanup on writing failures.
   Reader-only tests should call the read boundary when they specifically
   assert no output is created.
7. Completed: extend the opt-in sample check
   to write VTKHDF in a temporary directory, inspect all 10 animation steps,
   compare data against LTAT's decoded source, and verify the source hash.
   Do not write animation output beside the untracked sample.
8. Completed: run focused tests through `uv run --locked` and record results. Verify
   scale-dependent behavior separately with a larger input; do not claim
   VTK/ParaView interoperability unless an actual visualization reader is
   available and exercised.

Pause after each step for review. Converter delegation and focused tests
and generated-file output integration are implemented. Sample conversion
and data comparisons pass. ParaView 6.2.0's VTK HDF reader verifies all three
generated time steps and all ten sample time steps, including point/vertex
counts, positions, scalars, step numbers, and box arrays. All 31 focused
tests pass with the sample and ParaView checks enabled. Interactive rendering
and larger-scale behavior remain unverified.

Phases 1 and 2 are complete within the animation class boundary. The
CLI requirements for mandatory options, script invocation, and parser-side
input validation are implemented and verified.
Continue to pause after each step for review.

## Test Plan

1. The shared top-level parser exposes `lop_sf_fcc_animation`.
2. The required input and output options parse to the corresponding
   `Path` values.
3. Omitting either input or output option is rejected.
4. An unknown subcommand option is rejected.
5. The subparser sets `func` to the callable adapter.
6. Dispatch invokes the handler with the parsed namespace and preserves both
   paths unchanged.
7. `uv run ltaw.py` runs the CLI without a console-script entry point.
8. Invalid input-file values fail through the callable's validation and do
   not produce the placeholder conversion message.
9. Implemented: parser-side input existence and regular-file checks satisfy
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

- Final combined regression passed all 40 focused CLI/animation tests via
  `uv run --locked`, with sample and ParaView checks enabled, after both
  the script rename and parser-side validation changes.
- The subcommand accepts mandatory `--input-file` and
  `--output-vtkhdf-file`, both as `Path`. Positional input is
  rejected. All 24 focused CLI and animation unit tests passed at the earlier
  change, covering required arguments, help, parsing, and dispatch.
- The approved entry point is `ltaw.py`; no console script is declared.
  All 33 selected CLI/animation tests passed, including conversion from
  outside the repository with exit status zero and unchanged source data.
- Callable handler binding through `set_defaults(func=...)` and generic
  `args.func(args)` dispatch are implemented.
- Current parser, dispatch, and callable tests pass.
- Parser-side input-file existence and regular-file validation are implemented.
  All 37 selected CLI/animation tests passed, including missing files,
  directories, broken/valid symlinks, and input removal after parsing.
  Opt-in sample/ParaView checks were not rerun in this step.
- The low-level source API and lifecycle have been inspected in LTAT source.
- The user approved the registered source builder for Phase 1 and writer
  value-object builder for Phase 2; no new reader value-object layer is needed.
- Dependency integration and project-environment import/builder checks are
  complete; all 15 focused animation/CLI tests passed after synchronization.
- Reader delegation is implemented with focused builder, iteration, cleanup,
  and failure-propagation tests; all 18 animation/CLI tests passed.
- Generated real-file integration tests pass: repeated valid reads,
  non-HDF5 input, incompatible schema, and nonfinite final-frame data.
  All 22 focused animation/integration/CLI tests passed; the inputs remain
  unchanged and no VTKHDF output is created.
- Sample verification passed: 10 frames, 5849 atoms, steps 0..9, time step
  2.0 fs, and length units `Angstrom`. Source SHA-256 remained unchanged and
  no VTKHDF output was created. The sample test is opt-in via
  `LTAW_SAMPLE_HDF5`; normal focused suites pass with 22 tests and one skip.
- Final Phase 1 validation passed with all 23 focused tests, including the
  enabled local sample check, through `uv run --locked`.
- Phase 1 reader integration and validation are complete within the class
  boundary. Parser-side existence validation is also complete.
- Phase 2 converter delegation is implemented through LTAT's converter
  builder and its writer value-object path. Generated output data, existing
  target protection, and mid-write abort cleanup are verified through
  integration tests. Sample conversion also passed with all 10 steps compared
  against LTAT's decoded source, unchanged input SHA-256, and no staging
  residue. ParaView 6.2.0's VTK HDF reader also verified all generated/sample
  time steps and frame data; all 31 focused tests passed with both opt-in
  checks enabled.
- Phases 1 and 2 are complete within the animation class boundary.
  Interactive rendering and larger-scale behavior remain unverified.
  Parser-side validation and script invocation are also verified.
