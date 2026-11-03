 Top Level Plan - Command Line

This is the canonical standing plan for the command-line feature. It inherits
all project-wide rules from
[../../top_level_plan.md](../../top_level_plan.md) and adds feature-specific
rules; it must not weaken the project-wide rules.

## Objective

Maintain a command-line interface with a top-level parser and a distinct
subcommand for each simulation-analysis task. Each subcommand validates its
task-specific arguments and dispatches to the corresponding task
implementation. The entry point is
`scripts/ltaw.py`, invoked through `uv run scripts/ltaw.py`. It uses the shared
parser and dispatch flow rather than containing task-specific analysis or
conversion logic.

A task generally orchestrates this three-stage pipeline:

1. Select the relevant output files from a LAMMPS molecular dynamics
   simulation.
2. Use MDAnalysis to read those outputs and convert them into an HDF5 data
   file.
3. Convert the HDF5 data into VTKHDF files suitable for animation.

The pipeline is the general task shape; exact input files, options, and
conversion behavior are task-specific. Every value consumed by a task is
validated at the command line and again at CLI-class construction.

## CLI Contract

- Provide one distinct subcommand per task; subcommands must not collapse
  unrelated tasks behind a mode or task-name argument.
- Each subcommand owns its task-specific parser and passes validated values
  to its task implementation.
- Keep shared parsing and dispatch separate from task-specific LAMMPS,
  MDAnalysis, HDF5, and VTKHDF conversion logic.
- For tasks following the general pipeline, preserve the stage order:
  LAMMPS simulation outputs → MDAnalysis/HDF5 → VTKHDF animation outputs.
- Pass the output of each conversion stage explicitly to the next stage.
- Treat task inputs and outputs as explicit CLI/task configuration; do not
  silently substitute missing paths or conversion results.
- If a pipeline stage fails, do not report the task as successful or proceed
  as though that stage produced valid output. Surface the failure through the
  CLI's normal error path.
- Validate every value consumed by a task both during command-line parsing
  and at CLI-class construction.

## Implementation Structure

Feature workspace (plan, boundaries, and status only — no code):

```text
workspaces/features/command_line_workspaces/
  README.md
  context.md
  top_level_plan.md
  features/
    lop_sf_fcc_animation_subcommand_workspaces/
      README.md
      context.md
      top_level_plan.md
```

The current CLI scaffold and intended production boundary are:

```text
scripts/ltaw.py                                    # script entry point
src/
  lammps_trajectory_analysis_workspaces/
    ltaw_workspace_parser.py                # top-level parser and registration
    cli/
      cli_args.py                           # typed parsed-argument wrapper
      lop_sf_fcc_animation_subparser.py      # task parser and handler binding
    lop_sf_fcc_animation/
      animation.py                           # callable task boundary
tests/
  command_line/
    test_cli_arguments.py
  lop_sf_fcc_animation/
    test_animation.py
```

The script delegates generic dispatch to `ltaw_workspace_parser.run`;
no console script is declared.
Shared parser construction,
and per-task subcommand builders belong in
the package; task-specific LAMMPS, MDAnalysis, HDF5, and VTKHDF work remains
with task implementations. The `lop_sf_fcc_animation` subparser binds
`LopSfFccAnimation.run_from_cli_args` as its `func` handler. The main program
parses the selected subcommand and invokes `args.func(args)`, with no
command-name conditional.

The current animation callable validates the input file and path types,
retains the input and output paths, and delegates reading to LTAT's
registered source builder using context-managed full frame iteration.
Writing now delegates to LTAT's registered converter, which builds its
writer value object through the registered builder. Generated-file output
validation and 10-trajectory sample conversion pass. ParaView 6.2.0's
VTK HDF reader verifies all time steps and frame data for generated and
sample output; interactive rendering remains unverified. The animation work
was implemented in two phases: first
read the HDF5 trajectory through LTAT's existing reader, then write VTKHDF
through LTAT's existing writer. Both phases are complete within the animation
class boundary. Script-only invocation and existing-regular-file validation
at both parsing and constructor boundaries are verified.

## Test Plan

1. The top-level parser exposes registered task subcommands and requires a
   selected subcommand for normal execution; top-level help remains available.
2. The planned `lop_sf_fcc_animation` invocation is
   `uv run scripts/ltaw.py lop_sf_fcc_animation --input-file INPUT_FILE --output-vtkhdf-file OUTPUT_VTKHDF_FILE`.
   Both `--input-file` and `--output-vtkhdf-file` are mandatory `Path`
   options. Positional input is rejected.
3. Implemented: the script runs through `uv run scripts/ltaw.py`.
   The user chose script-only invocation and the non-conflicting name.
   Verify successful conversion and exit status from outside the repository.
4. Each subparser binds its callable handler using `set_defaults(func=...)`;
   the entry point dispatches with `args.func(args)`.
5. Parsed values are propagated unchanged to the matching task implementation
   and validated both during argument processing and at callable-class
   construction. The current animation command still needs CLI-side
   validation that its input path is an existing regular file.
6. For a task using the general pipeline, verify stage order and explicit
   propagation of LAMMPS inputs to HDF5 conversion and HDF5 output to VTKHDF
   conversion.
7. A failed stage is surfaced as a CLI failure; later stages are not invoked
   with missing or invalid output.
8. CLI contract tests do not require production LAMMPS trajectory files when
   stage collaborators can be replaced with controlled test doubles.
9. Implement the LOP-SF-FCC animation in sequence: complete and verify
   external HDF5 reading first, then integrate external VTKHDF writing.

## Non-Goals

- Do not implement LAMMPS parsing or MDAnalysis conversion inside the shared
  argument parser.
- Do not force every task to share identical simulation files, CLI options,
  or conversion details beyond the general three-stage pipeline.
- Do not merge distinct tasks into one generic subcommand.
- Do not define task-specific output naming, intermediate retention, or
  overwrite policies until those requirements are established by the task.

## Acceptance Criteria

- The CLI contract describes one distinct subcommand per task.
- The command accepts mandatory HDF5 input and VTKHDF output options,
  reads the input trajectory, and writes the requested output.
- The command is runnable with the documented `uv run scripts/ltaw.py`
  invocation without an installed console-script entry point.
- The subcommand uses handler-based dispatch.
- The general task pipeline is documented in order: LAMMPS outputs,
  MDAnalysis-to-HDF5, then HDF5-to-VTKHDF for animation.
- Task-specific parsing and dispatch remain separate from domain conversion
  implementations.
- Invalid inputs and stage failures are surfaced rather than producing a
  success-shaped result.
- Tests cover subcommand discovery, required arguments, handler
  registration, dispatch, and constructor-level invalid input behavior.
  Parser-side regular-file checks, post-parse removal, HDF5 reading, and
  VTKHDF writing are also covered. All 37 selected tests passed after adding
  parser validation; opt-in sample/ParaView checks were not rerun in that step.
