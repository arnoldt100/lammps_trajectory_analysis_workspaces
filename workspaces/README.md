# Project Layouts Index

This file serves as the central index for all physical layouts, cells, and blocks within this ICM workspace.

Use it to locate the owning workspace for any production file before reading
or editing code: find the file's feature in the Layout Index below, then read
that feature's `context.md` (current status), `top_level_plan.md` (standing
rules and contract), and `README.md` (goal, boundaries, dependencies) — in
that order, and nothing else unless the feature's own files point further.
This keeps operational context scoped to one feature folder.

## File Roles (every feature folder)

- `README.md` — feature goal, structural boundaries (owned `src/` and
  `tests/` paths), external dependencies, cross-feature dependencies.
- `context.md` — implementation status snapshot (Done/Pending/Not planned),
  decision log, data-flow sketch, maintenance rule.
- `top_level_plan.md` — standing rules, contracts, test plan, non-goals,
  acceptance criteria, migration log. Child plans must not weaken their
  parent plan.

## Workspace Directory Structure

```text
.
├── README.md                      # this file — central index
│
├── context.md                     # ICM root purpose, folder conventions, working rules
│
├── top_level_plan.md              # project-wide engineering rules (all features inherit)
│
├── features/
    └──
```


## Layout Index & Status

| Feature | Workspace | Owned production code | Owned tests | Status |
|---|---|---|---|---|
|   |   |   |   |   |
