# ICM Workspaces Index

This directory is the root of the repository's Interpretable Context
Methodology (ICM) workspace documentation.

## Root Documents

- [context.md](context.md) — purpose and organization of this workspace.
- [top_level_plan.md](top_level_plan.md) — project-wide rules inherited by
  all feature plans.

## Directory Structure

The workspace tree follows the package and feature hierarchy under
`src/lammps_trajectory_analysis_workspaces/`. Collection workspaces own
shared package boundaries; child feature workspaces live in their parent's
`features/` directory and describe narrower package areas.

```text
workspaces/
  README.md
  context.md
  top_level_plan.md
  features/
    command_line_workspaces/
      README.md
      context.md
      top_level_plan.md
      cli_args_implementation_plan.md
      lop_sf_fcc_animation_subcommand_plan.md
      features/
        lop_sf_fcc_animation_subcommand_workspaces/
          README.md
          context.md
          top_level_plan.md
    design_patterns_workspaces/
      context.md
      top_level_plan.md
      features/
        builder_design_pattern/
          README.md
          context.md
          top_level_plan.md
        value_semantics/
          README.md
          context.md
          top_level_plan.md
```

## Feature Index

| Feature | Workspace | Owned production code | Owned tests | Status |
|---|---|---|---|---|
| Command line | [features/command_line_workspaces/](features/command_line_workspaces/README.md) | Entry point, shared parser, CLI argument wrapper, command subparsers and dispatch | `tests/command_line/` | Active; `lop_sf_fcc_animation` subcommand implemented, conversion deferred |
| LOP-SF-FCC animation subcommand | [features/command_line_workspaces/features/lop_sf_fcc_animation_subcommand_workspaces/](features/command_line_workspaces/features/lop_sf_fcc_animation_subcommand_workspaces/README.md) | `src/lammps_trajectory_analysis_workspaces/cli/lop_sf_fcc_animation_subparser.py` | `tests/command_line/test_cli_arguments.py` | Active; parser-side input existence validation pending |
| Design-pattern templates | [features/design_patterns_workspaces/](features/design_patterns_workspaces/context.md) | `src/lammps_trajectory_analysis_workspaces/design_patterns_templates/` | `tests/design_patterns_templates/` | Active |
| Builder design pattern | [features/design_patterns_workspaces/features/builder_design_pattern/](features/design_patterns_workspaces/features/builder_design_pattern/README.md) | `design_patterns_templates/builder/` | `tests/design_patterns_templates/builder/` | Implemented; timer migration complete |
| Value semantics | [features/design_patterns_workspaces/features/value_semantics/](features/design_patterns_workspaces/features/value_semantics/README.md) | `design_patterns_templates/value_semantics/` | `tests/design_patterns_templates/value_semantics/` | Implemented |

Use each workspace's `context.md`, `top_level_plan.md`, and `README.md` as
the current status, standing contract, and boundary/dependency guide,
respectively. Collection workspaces may use a subset of those documents when
their role is an index or shared-rule parent rather than a standalone
implementation feature.
