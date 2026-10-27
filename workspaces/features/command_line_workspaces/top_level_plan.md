 Top Level Plan - Command Line

This is the canonical standing plan for the command-line feature. It inherits
all project-wide rules from
[../../top_level_plan.md](../../top_level_plan.md) and adds feature-specific
rules; it must not weaken the project-wide rules.

## Objective

Maintain a command-line interface with a top-level parser and a distinct
subcommand for each simulation-analysis task. Each subcommand validates its
task-specific arguments and dispatches to the corresponding task
implementation.

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

## Package Structure

Feature workspace (plan, boundaries, and status only — no code):

```text
workspaces/features/command_line_workspaces/
  README.md
  context.md
  top_level_plan.md
```

The planned production boundary is the CLI entry point, top-level parser,
per-task subcommand builders, and CLI-level orchestration/dispatch under
`src/lammps_trajectory_analysis_workspaces/`. Tests are centralized under
`tests/`. Record exact file paths here and in the feature README when the
implementation structure is established.

## Test Plan

1. The top-level parser exposes the registered task subcommands.
2. Each task subcommand parses and validates its own required inputs and
   options, and rejects invalid values.
3. Parsed values are propagated unchanged to the matching task implementation
   and are validated again at CLI-class construction.
4. For a task using the general pipeline, verify stage order and explicit
   propagation of LAMMPS inputs to HDF5 conversion and HDF5 output to VTKHDF
   conversion.
5. A failed stage is surfaced as a CLI failure; later stages are not invoked
   with missing or invalid output.
6. CLI contract tests do not require production LAMMPS trajectory files when
   stage collaborators can be replaced with controlled test doubles.

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
- The general task pipeline is documented in order: LAMMPS outputs,
  MDAnalysis-to-HDF5, then HDF5-to-VTKHDF for animation.
- Task-specific parsing and dispatch remain separate from domain conversion
  implementations.
- Invalid inputs and stage failures are surfaced rather than producing a
  success-shaped result.
- Tests cover subcommand discovery, validation, dispatch, pipeline ordering,
  and failure behavior.
