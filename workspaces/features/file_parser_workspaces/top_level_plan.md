# Top-Level Plan - File Parser

This feature inherits the [project-wide rules](../../top_level_plan.md).
This document defines the planned contract. See [current context](context.md)
for verified implementation status.

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
- Option names must be supplied in full; disable argparse abbreviation.
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
    file_parser_options.py
    json_file_parser.py
tests/
  file_parser/
    test_file_parser_options.py
    test_json_file_parser.py
  command_line/
    test_create_batch_file.py
```

Define the shared options dataclass in
`lammps_trajectory_analysis_workspaces.file_parser.file_parser_options` so the script
and conversion module can import it without the library importing the
entry-point script:

```python
@dataclass
class FileParserOptions:
    input_file: Path
    output_file: Path
    json_file: Path
```

The fields above are required `Path` values with no defaults.
Re-export `FileParserOptions` from the `file_parser` package for convenient
shared imports.

The standalone script defines the parsing function:

```python
def parse_command_line_arguments(
    argv: Sequence[str] | None = None,
) -> FileParserOptions:
    ...
```

With `argv=None`, argparse reads the process arguments; an explicit
sequence supports focused tests and programmatic parsing. The function
returns a `FileParserOptions` instance, not an argparse namespace, and
performs no conversion or source/output file I/O.

The proposed conversion callable is:

```python
def create_output_file(options: FileParserOptions) -> None:
    ...
```

It belongs to
`lammps_trajectory_analysis_workspaces.file_parser.json_file_parser`.
It reads paths from the dataclass, reads both source files, validates the
replacement contract, performs substitution, and creates the requested
output. It does not mutate the options, parse process arguments, print
diagnostics, or terminate the process. Programmatic callers construct the
same dataclass without invoking command-line parsing.

The script imports the `json_file_parser` module from the `file_parser`
package. Its main function calls `parse_command_line_arguments()` and
passes the returned object to `json_file_parser.create_output_file(options)`
without unpacking it into separate arguments. Follow the existing
standalone script's source-tree import convention so invocation works
outside the repository working directory as well.

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

Implementation is divided into two stages. Stage 1 is authorized in
reviewable phases; Stage 2 awaits a separate implementation request.

### Stage 1 - Command-Line Parsing

Review phases:

1. Shared `FileParserOptions` dataclass and focused contract tests.
2. Parsing function and focused argument-parsing tests.
3. Main-function and entry-point wiring, standalone invocation tests, and
   parsing-only usage documentation.

Phase 3 is implemented and verified, pending user review. See
[current context](context.md) for verification results.

Stop after each completed phase for user review and approval before
starting the next phase.

1. Add the `file_parser` package with the shared `FileParserOptions`
   dataclass. Implement `parse_command_line_arguments` in the standalone
   script for the required `--input-file`, `--output-file`, and `--json-file`
   options, each parsed as `pathlib.Path`, and return the dataclass.
2. Keep parsing separate from conversion so the returned dataclass can be
   passed to the module in Stage 2. Use the existing source-tree import
   convention to import the shared dataclass. Do not read source files,
   validate JSON, create output, or import the not-yet-implemented
   conversion module.
3. Fix the entry-point guard to invoke the main function. Provide standard
   argparse help, missing-option diagnostics, and unknown-option diagnostics.
   During Stage 1, main returns the parsed options for programmatic use;
   the guard calls main without passing that object to `sys.exit`.
   Help explicitly identifies the parsing-only limitation.
4. Add focused parsing and standalone invocation tests, including invocation
   outside the repository working directory.
5. Document the parsing-only milestone and its limitations. A valid
   invocation completes parsing only; it must not claim a batch file was
   generated.

Stage 1 is complete when the parsing function returns a `FileParserOptions`
instance containing all three supplied paths as `Path` values, help works,
argument errors exit with status 2, and parsing performs no conversion or
source/output file I/O. The complete public command contract above is
delivered only after Stage 2.

### Stage 2 - Passing Arguments to the JSON File Module

Depends on Stage 1.

1. Add `json_file_parser.create_output_file(options: FileParserOptions)` to
   the Stage 1 package using the standard library. Implement the JSON
   validation, literal substitution, file handling, and error contracts
   above.
2. Import the `json_file_parser` module using the existing standalone
   source-tree import convention. Pass the dataclass returned by
   `parse_command_line_arguments` directly to `create_output_file`,
   without unpacking the paths or moving argument parsing into the module.
3. Translate expected conversion errors into explicit stderr diagnostics
   and nonzero exit status; successful conversion exits with status 0.
4. Add library tests and extend the Stage 1 CLI tests with module delegation,
   successful conversion, and conversion-failure coverage.
5. Document complete usage in the project README and update workspace
   status only after implementation is verified.

Stage 2 is complete when the standalone command generates the expected
output through the module, preserves the file-safety guarantees, reports
failures explicitly, and passes the library and end-to-end CLI tests.

## Verification Plan

Library tests must cover:

- Calling the conversion API with a constructed `FileParserOptions`
  instance, without invoking the script or changing the options.
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

Stage 1 CLI tests must cover:

- Help, all required options, absent options, and unknown options.
- The parsing function returns a `FileParserOptions` instance containing
  the expected `Path` fields, not an argparse namespace.
- Explicit argument sequences and default process-argument parsing.
- Relative paths remain relative to the process working directory.
- Actual standalone script invocation through the entry-point guard.
- Invocation from a working directory outside the repository.
- Parsing alone does not read input or JSON files or create output.

Stage 2 retains the Stage 1 parsing coverage, replaces parsing-only
invocation expectations with conversion expectations, and adds:

- Correct module delegation with the same dataclass object returned by
  the parsing function, containing all three parsed paths.
- Successful output content and exit status.
- Conversion failures with stderr diagnostics and nonzero exit status.

Run the smallest relevant test selection through `uv run`.

For Stage 1:

```text
uv run python -m pytest tests/file_parser/test_file_parser_options.py tests/command_line/test_create_batch_file.py
```

For Phase 1 alone, run only `tests/file_parser/test_file_parser_options.py`.
The CLI test file is present as of Phase 2.

For Stage 2:

```text
uv run python -m pytest tests/file_parser tests/command_line/test_create_batch_file.py
```

Include existing command-line tests when verifying that the shared CLI
behavior is preserved. Documentation-only updates need no execution tests.
