# Context - Command-Line Feature

Status snapshot and decision log for the command-line feature. Update this
file whenever the feature's behavior, data flow, or boundaries change.

## Implementation Status

### Done

- The intended task workflow and three-stage pipeline are documented.

### Pending

- Implement the top-level CLI parser and task-specific subcommands.
- Connect each subcommand to its task implementation and the three-stage
  conversion pipeline.
- Add contract and orchestration tests.
- Record the concrete source/test paths and task-specific arguments in the
  feature README and plan as they are established.

### Not planned

## Decisions

- Each task has a distinct subcommand.
- A task generally consists of selecting LAMMPS simulation output files,
  using MDAnalysis to read them and produce HDF5 data, then converting that
  HDF5 data into VTKHDF files for animation.
- Task-specific inputs and options belong to their corresponding subcommand;
  shared parsing and dispatch remain in the CLI feature.
- Existing plan contract is retained: values consumed by a task are
  validated at the command line and again when its CLI-facing class is
  constructed.

## Current Data Flow

```text
user invokes task subcommand
        │
        ├─ parse and validate task-specific arguments
        ▼
select relevant LAMMPS simulation output files
        │
        ▼
MDAnalysis reads selected outputs and produces HDF5 data
        │
        ▼
convert HDF5 data into VTKHDF files for animation
```

The exact file formats, arguments, and conversion implementations are
task-specific and remain to be recorded when each task is defined.

## Maintenance Rule

When adding or changing a subcommand or pipeline stage, update its contract
and arguments in `top_level_plan.md`, the implementation boundaries and
dependencies in `README.md`, and this status/data-flow snapshot. Keep tests
aligned with parser validation, task dispatch, stage ordering, and propagation
of stage inputs and outputs.