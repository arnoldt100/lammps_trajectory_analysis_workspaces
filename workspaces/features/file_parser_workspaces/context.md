# Context - File Parser

## Status

Stage 1, all three phases are implemented, verified, and approved.
The main function calls the parser and returns its
`FileParserOptions`; the entry-point guard invokes main. Help, argument
errors, and parsing-only invocation work inside and outside the repository.
Five options tests, thirty-seven parsing and invocation tests, and
twenty-one existing CLI tests pass (63 total).
Stage 2, Phase 1 is approved.
The JSON module validates replacement maps and renders template text in
memory, with 49 focused tests. Phase 2 is implemented and verified, pending
user review: `create_output_file(options)` reads UTF-8 sources, validates
and encodes the complete result before exclusive output creation, preserves
line endings, and removes incomplete output after write or close failures.
Cleanup failures report both the original failure and cleanup failure.
There are 41 additional file-handling tests; all 153 file-parser and CLI
tests pass. CLI conversion integration is not implemented; the standalone
command still performs parsing only.

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
- JSON keys include the delimiters, for example
  `{"__JOB_NAME__": "analysis"}`.
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

Await Stage 2, Phase 2 review and approval. Phase 3 integrates conversion
into the CLI and updates usage documentation. Follow
[the implementation plan](top_level_plan.md).
Neither stage changes the existing analysis CLI.
