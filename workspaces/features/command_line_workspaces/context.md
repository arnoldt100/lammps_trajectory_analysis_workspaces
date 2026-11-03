# Context - Command-Line Feature

Status snapshot and decision log for the command-line feature. Update this
file whenever the feature's behavior, data flow, or boundaries change.

## Implementation Status

### Done

- Current invocation is `uv run scripts/ltaw.py lop_sf_fcc_animation --input-file
  INPUT_FILE --output-vtkhdf-file OUTPUT_FILE` from the project root.
  Both options are mandatory. All 41 selected tests passed after this
  change, including exact-invocation conversion and outside-directory
  script conversion; sample/ParaView checks were not rerun.
- Final combined regression after the script rename and parser validation:
  all 40 focused CLI/animation tests passed through `uv run --locked`, with
  `LTAW_SAMPLE_HDF5` and `LTAW_PVPYTHON` enabled. This includes sample
  conversion, generated/sample ParaView reader comparisons, script dispatch,
  input validation, existing-output protection, and write-failure cleanup.
- The intended task workflow and three-stage pipeline are documented.
- Entry point implemented at
  `scripts/ltaw.py`.
- Shared parser implemented at
  `src/lammps_trajectory_analysis_workspaces/ltaw_workspace_parser.py`.
- Added `cli_args.py` with the parsed namespace wrapper.
- Registered `lop_sf_fcc_animation` with mandatory `--input-file`
  and `--output-vtkhdf-file` options, both parsed as `Path`.
  Positional input is rejected.
- Positional parsing, required arguments, help output, handler dispatch,
  and animation unit tests pass: 24 tests through `uv run --locked`.
- Subparser-specific ICM docs live in
  `workspaces/features/command_line_workspaces/features/lop_sf_fcc_animation_subcommand_workspaces/`;
  this parent workspace covers the shared top-level parser.
- Bound the command to `LopSfFccAnimation.run_from_cli_args` via
  `set_defaults(func=...)`; the main program dispatches with `args.func(args)`.
- Added the callable animation boundary, which validates/stores its paths and
  now reads through LTAT's registered HDF5 source builder using
  context-managed full frame iteration. The write method now delegates to
  LTAT's registered converter. Generated output data, existing-file
  protection, and mid-write abort cleanup are verified. The 10-trajectory
  sample conversion and data comparisons pass. ParaView 6.2.0's VTK HDF
  reader also verifies all generated/sample time steps, point/vertex
  counts, positions, scalars, step numbers, and box arrays against LTAT.
  All 31 focused tests pass with the sample and ParaView checks enabled.
  Interactive rendering and larger-scale behavior remain unverified.
  Reader-only checks create no output; conversion checks create output only
  in temporary directories. Source hashes remain unchanged.
- Added CLI and animation contract tests; the focused test suites pass.
- Input paths are checked for existence and regular-file status during
  parsing and again at callable construction. Missing paths, directories,
  and broken symlinks produce argparse errors (exit status 2); valid file
  symlinks retain their supplied paths. Removal after parsing is rejected
  at construction. All 37 selected CLI/animation tests passed; the opt-in
  sample and ParaView checks were not rerun in this step.

### Pending

- Interactive rendering and larger-scale behavior remain unverified;
  Phase 1 and Phase 2 are complete within the animation class boundary.

### Not planned

## Decisions

- Each task has a distinct subcommand.
- The entry point is `scripts/ltaw.py`, which delegates to the package's
  `ltaw_workspace_parser.run`, preserving its `CLIArgs` return. The user requested
  removal of `cli/main.py`, and chose script-only invocation.
- The package parser module owns top-level parser and subcommand construction;
  task-specific logic stays outside the entry-point script.
- `lop_sf_fcc_animation` uses `set_defaults(func=...)` and the main program
  dispatches by invoking the parsed handler with the parsed namespace.
- Planned invocation:
  `uv run scripts/ltaw.py lop_sf_fcc_animation --input-file INPUT_FILE --output-vtkhdf-file OUTPUT_VTKHDF_FILE`.
- For the current contract, `--input-file` is mandatory and the command reads
  it as HDF5 LOP-SF-FCC input, then writes the specified VTKHDF output.
- Implement in two phases: first read the HDF5 trajectory through the
  existing LTAT reader and verify this phase; only then implement VTKHDF
  writing through LTAT's `vtkhdf_writer`.
- Reuse LTAT's existing reader/writer packages; keep their domain logic out
  of this project.
- The user approved LTAT's existing composition: registered source builder
  for Phase 1 and registered writer value-object builder for Phase 2 through
  its converter. No new reader value-object layer is required.
- Pause after each step for review and approval.
- LTAT's canonical reader/writer package is
  `lib.lop_sf_fcc_vtkhdf_writer` under lowercase `src/`, not the previously
  recorded nested `lib/lop_sf_fcc/vtkhdf_writer` location. The reader offers
  context-managed opening and lazy frame iteration. Sample verification
  confirmed 10 frames, 5849 atoms per frame, and steps 0..9.
- No console script is declared in `pyproject.toml`. All 33 selected
  CLI/animation tests pass after the rename, including script conversion
  from outside the repository. Sample/ParaView checks were not rerun.
- The top-level parser requires a subcommand during normal execution.
- A task generally consists of selecting LAMMPS simulation output files,
  using MDAnalysis to read them and produce HDF5 data, then converting that
  HDF5 data into VTKHDF files for animation.
- Task-specific inputs and options belong to their corresponding subcommand;
  shared parsing and dispatch remain in the CLI feature.
- Feature contract: values consumed by a task are validated at the command
  line and again when its CLI-facing class is constructed. For the current
  animation command, existing-regular-file validation is implemented at
  both boundaries. HDF5 schema/content validation remains with LTAT.

## Current Data Flow

```text
user invokes task subcommand
        │
        ▼
scripts/ltaw.py
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