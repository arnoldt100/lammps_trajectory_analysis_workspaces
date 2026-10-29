# CLI Arguments Implementation Plan

## Implementation Record

This plan describes the initial argument-processing implementation. That
work is complete, and the CLI has since grown to include the
`lop_sf_fcc_animation` subcommand. The current implementation is described in
the command-line feature's
[top-level plan](top_level_plan.md) and
[`lop_sf_fcc_animation` plan](lop_sf_fcc_animation_subcommand_plan.md).

## Planned Changes

### 1. Add `CLIArgs`

Create
`src/lammps_trajectory_analysis_workspaces/cli_args.py` with a minimal typed
`CLIArgs` class to represent successfully parsed command-line values.

Do not add speculative task or option fields yet. Extend the class with
explicitly typed fields when the corresponding CLI options are established.

### 2. Add argument processing

In
`src/lammps_trajectory_analysis_workspaces/ltaw_workspace_parser.py`, add
`process_command_line_arguments(argv=None)`.

The initial parser implementation:

- Create and configure the top-level `argparse.ArgumentParser`.
- Relied on argparse's built-in `-h` and `--help` options.
- Parse the supplied arguments and return a `CLIArgs` instance for normal
  execution.
- Accept `argv=None` so production uses `sys.argv`, while tests can provide
  arguments directly.

Help requests retain argparse's standard behavior: print help and exit
successfully instead of returning `CLIArgs`.

### 3. Wire the entry point

Update `main()` in
`ltaw.py` to call
`process_command_line_arguments`. No analysis dispatch is added until task
subcommands exist. Correct the script's malformed shebang as part of making
the entry point executable.

### 4. Add focused tests — complete

Add CLI tests under `tests/` to verify:

1. Parsing an empty argument list returns a `CLIArgs` instance.
2. Both `-h` and `--help` display help and exit successfully.
3. Unknown arguments are rejected.
4. `main()` invokes argument processing.

Tests should pass argument lists directly where possible and avoid dependence
on production simulation files.

### 5. Update feature documentation

After implementation paths are established, update the command-line feature
README, context, and top-level plan to identify the `CLIArgs` module and
document the initial parser behavior. Keep the standing contract for distinct
future task subcommands and task-specific validation.

## Historical Scope Boundaries

- The initial change did not add task subcommands; they are now tracked in
  the dedicated `lop_sf_fcc_animation` plan.
- No LAMMPS, MDAnalysis, HDF5, or VTKHDF processing.
- No task dispatch or pipeline implementation was part of the initial change.
- No speculative `CLIArgs` fields.

## Completion Criteria

- `process_command_line_arguments(argv=None)` constructs the top-level
  parser and returns `CLIArgs` for valid normal input.
- `-h` and `--help` use argparse's standard help-and-exit behavior.
- Unknown arguments fail through argparse's normal error handling.
- `main()` calls the argument processor.
- The focused tests pass and the feature documentation matches the
  implementation.

Status: the initial CLI argument-processing work is complete. Subsequent
subcommand behavior is tracked separately.
