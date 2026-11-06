# Context - File Parser

## Status

Planning only. No production code or tests have been changed for this
feature. The existing batch-file script is a stub.

## Purpose

Create a Slurm batch file from a text template and a JSON replacement map.
Keep command-line handling separate from reusable file-conversion logic.

## Confirmed Decisions

- Canonical names are `create_batch_file.py`, `file_parser`, and
  `json_file_parser.py`. Earlier `jsan`, `jason`, and `create_bathc_file`
  spellings were typographical errors.
- The standalone script requires `--input-file`, `--output-file`, and
  `--json-file`.
- `parse_command_line_arguments` lives in the standalone script and returns
  a shared `FileParserOptions` dataclass with three required `Path` fields:
  `input_file`, `output_file`, and `json_file`.
- Define the dataclass in `file_parser.__init__`, not in the script.
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
- Only ICM planning documents are authorized at this stage.

## Next Implementation Work

Follow [the implementation plan](top_level_plan.md) after implementation
is requested. Stage 1 adds the shared options dataclass and implements and
tests command-line parsing only, without source/output file I/O. Stage 2
implements the JSON file module, passes the returned dataclass to it, and
verifies library and end-to-end CLI behavior.
Neither stage changes the existing analysis CLI.
