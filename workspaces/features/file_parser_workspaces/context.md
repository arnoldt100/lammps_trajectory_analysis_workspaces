# Context - File Parser

## Status

Stage 1, all three phases are implemented, verified, and approved.
The parser returns `FileParserOptions`; the entry-point guard invokes main.
Stage 2, Phases 1 and 2 are approved.
The JSON module validates replacement maps and renders template text in
memory, with 49 focused tests. `create_output_file(options)` reads UTF-8 sources, validates
and encodes the complete result before exclusive output creation, preserves
line endings, and removes incomplete output after write or close failures.
Cleanup failures report both the original failure and cleanup failure.
There are 41 additional file-handling tests. Phase 3 is implemented,
verified, and approved: main passes the same parsed dataclass directly
to the JSON module and returns it after successful conversion. Expected
conversion errors (`OSError` and `ValueError`, including JSON and Unicode
errors) produce concise stderr diagnostics and exit status 1. Unexpected
errors propagate. Help and successful conversion exit with status 0;
argument errors exit with status 2. Usage documentation describes conversion.
All 182 file-parser and CLI tests pass, including standalone invocation
inside and outside the repository.

## Purpose

Create a Slurm batch file from a text template and a JSON replacement map.
Keep command-line handling separate from reusable file-conversion logic.

## Confirmed Decisions

- Canonical names are `create_batch_file.py`, `file_parser`, and
  `json_file_parser.py`. Earlier `jsan`, `jason`, and `create_bathc_file`
  spellings were typographical errors.
- The standalone script requires `--input-file`, `--output-file`, and
  `--json-file`.
- Reject abbreviated option names as unknown arguments rather than using
  argparse's optional prefix matching.
- `parse_command_line_arguments` lives in the standalone script and returns
  a shared `FileParserOptions` dataclass with three required `Path` fields:
  `input_file`, `output_file`, and `json_file`.
- Define the dataclass in its own `file_parser.file_parser_options` module,
  and re-export it from the package, not from the script.
  Pass the returned object directly to `json_file_parser.create_output_file`.
- Replacement files may contain `data =` followed by a JSON object with
  undelimited, case-sensitive keys such as `"jobname"` for `__jobname__`.
  Standalone JSON objects remain supported with fully delimited keys, for
  example `{"__JOB_NAME__": "analysis"}`.
- Match placeholders independently, rather than using the greedy
  `__(.*)__` literally.
- Values are strings; substitution is literal and single-pass.
- A placeholder without a replacement is an error.
- Unused JSON keys are permitted.
- Existing output must not be overwritten.
- Validate the template and JSON before creating output.
- Implement in two stages: standalone command-line parsing first, then
  passing the options dataclass to the JSON file module for conversion.
- Implement both stages in phases, stopping for user review and approval
  after each completed phase before starting the next.

## Next Implementation Work

Both stages and all review phases are implemented, verified, and approved.
No further implementation phase is planned. See
[the implementation plan](top_level_plan.md).
Neither stage changes the existing analysis CLI.
