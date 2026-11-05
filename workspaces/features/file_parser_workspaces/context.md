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
- JSON keys include the delimiters, for example
  `{"__JOB_NAME__": "analysis"}`.
- Match placeholders independently, rather than using the greedy
  `__(.*)__` literally.
- Values are strings; substitution is literal and single-pass.
- A placeholder without a replacement is an error.
- Unused JSON keys are permitted.
- Existing output must not be overwritten.
- Validate the template and JSON before creating output.
- Only ICM planning documents are authorized at this stage.

## Next Implementation Work

Follow [the implementation plan](top_level_plan.md) after implementation
is requested. Add the package, complete the standalone script, and verify
unit and subprocess tests without changing the existing analysis CLI.
