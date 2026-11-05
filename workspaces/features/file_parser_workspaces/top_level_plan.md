# Top-Level Plan - File Parser

This feature inherits the [project-wide rules](../../top_level_plan.md).
This document defines the planned contract; it does not claim that the
implementation exists.

## Objective

Generate a Slurm batch file by substituting JSON-provided strings into a
text template. The reusable module owns the complete conversion; the
standalone script owns only the command-line boundary.

## Public Command Contract

```text
uv run "$LTAW_TOP_LEVEL/scripts/create_batch_file.py" \
  --input-file <path_to_input_file> \
  --output-file <path_to_output_file> \
  --json-file <path_to_json_file>
```

- All three options are required and parsed as `pathlib.Path`.
- Relative paths are relative to the process working directory.
- Missing required options and unknown options use standard argparse
  diagnostics and exit status 2.
- Conversion succeeds with exit status 0.
- Invalid JSON, invalid replacements, missing input files, an existing
  output path, and other conversion or I/O failures produce an explicit
  stderr diagnostic and nonzero exit status.
- The entry-point guard must actually invoke the main function.
- Do not add a `ltaw.py` subcommand or an installed console command.

## Package and API Boundary

Planned layout:

```text
scripts/
  create_batch_file.py
src/lammps_trajectory_analysis_workspaces/
  file_parser/
    __init__.py
    json_file_parser.py
tests/
  file_parser/
    test_json_file_parser.py
  command_line/
    test_create_batch_file.py
```

The proposed callable is:

```python
create_output_file(
    input_file: Path,
    output_file: Path,
    json_file: Path,
) -> None
```

It belongs to
`lammps_trajectory_analysis_workspaces.file_parser.json_file_parser`.
It reads both source files, validates the replacement contract, performs
substitution, and creates the requested output. It does not parse process
arguments, print diagnostics, or terminate the process.

The script imports the `json_file_parser` module from the `file_parser`
package and delegates to this callable. Follow the existing standalone
script's source-tree import convention so invocation works outside the
repository working directory as well.

## JSON and Replacement Contract

Example template:

```text
#!/bin/bash
#SBATCH --job-name=__JOB_NAME__
#SBATCH --time=__WALLTIME__
echo "__JOB_NAME__"
```

Example JSON:

```json
{
  "__JOB_NAME__": "analysis",
  "__WALLTIME__": "01:00:00"
}
```

- The top-level JSON value must be an object mapping fully delimited
  placeholder strings to string values. Reject invalid key shapes and
  non-string values; do not silently coerce them.
- Interpret placeholders using the non-greedy pattern `__(.*?)__`, without
  DOTALL, so multiple placeholders on a line are independent and matches do
  not span lines. JSON keys must fully match this same placeholder syntax.
- Each occurrence is replaced, including repeated placeholders.
- A matched placeholder missing from JSON is an error. Validate all matches
  before creating output.
- Unused JSON keys are allowed.
- Substitution is a single pass over the original template. Replacement
  strings containing placeholder-like text are not processed recursively.
- Replacement strings are literal: backslashes, dollar signs, and other
  regex or shell characters have no special replacement meaning.
- Do not perform shell expansion, escaping, expression evaluation, Slurm
  validation, or job submission.
- Text outside matched placeholders remains unchanged. A template with no
  matched placeholders is copied unchanged, subject to valid JSON.

## File Handling and Errors

- Read and write UTF-8 text and preserve template line endings and trailing
  newline presence.
- Read and validate both source files and finish substitution before
  opening the output.
- Refuse any existing output entry, including symlinks. Use exclusive
  creation, not only a prior existence check, to prevent race-based
  overwriting. This also protects input and JSON files when paths coincide.
- Require the output parent directory to exist; do not create directory
  trees implicitly.
- Report filesystem and decoding failures explicitly. The library raises
  errors; the script translates expected conversion errors into concise
  command-line diagnostics without a broad catch-all.
- Never report success after a failed write. Validation failures must not
  create output or alter existing files. If a write fails after creation,
  remove only the incomplete output created by that invocation and surface
  any cleanup failure.

## Implementation Sequence

1. Add the package and callable, implementing JSON validation and independent
   literal substitution using the standard library.
2. Add file handling with pre-write validation and exclusive output creation.
3. Complete the standalone script with required options, module delegation,
   explicit errors, and a working entry-point guard.
4. Add focused library and standalone CLI tests.
5. Document usage in the project README and update workspace status only
   after implementation is verified.

## Verification Plan

Library tests must cover:

- Exact expected Slurm output for a representative template and JSON map.
- Multiple placeholders on one line, adjacent placeholders, repeated
  placeholders, and placeholders on separate lines.
- Literal replacement of backslashes and dollar signs, empty replacement
  strings, Unicode text, and non-recursive replacement values.
- A template without placeholders and unused JSON keys.
- Missing replacements, malformed JSON, non-object JSON, invalid key shapes,
  and non-string values, with no output created.
- Missing or unreadable source files, UTF-8 decoding failures, missing output
  parent directories, and explicit propagation of write failures.
- Existing output files and symlinks, including output equal to an input
  path, remain unchanged.
- LF and CRLF line endings and presence or absence of a final newline.
- Removal of incomplete output after a failed write without deleting
  pre-existing files.

CLI tests must cover:

- Help, all required options, absent options, and unknown options.
- Actual standalone script invocation and correct module delegation.
- Invocation from a working directory outside the repository.
- Successful output content and exit status.
- Conversion failures with stderr diagnostics and nonzero exit status.

Run the smallest relevant test selection through `uv run`, initially:

```text
uv run python -m pytest tests/file_parser tests/command_line/test_create_batch_file.py
```

Include existing command-line tests when verifying that the shared CLI
behavior is preserved. No execution tests are needed for this planning-only
change.
