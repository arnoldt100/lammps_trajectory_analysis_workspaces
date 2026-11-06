# lammps_trajectory_analysis_workspaces
This repository contains scripts and programs that support LAMMPS trajectory analysis workflows across different computers.


## Quick Start
Setting up virtual environment for python >= 3.14
```
rm -rf ./.venv # Remove the old virtual environment
uv python install 3.14t # Install the free threaded python version
uv python pin 3.14t # Lock the python version.
uv run python -c "import sys; print('GIL Enabled:', sys._is_gil_enabled())" # Ensure the GIL is disabled.
```
## Documentation

### Batch File Command (Stage 1: Parsing Only)

```sh
uv run "$LTAW_TOP_LEVEL/scripts/create_batch_file.py" \
  --input-file template.slurm \
  --output-file batch.slurm \
  --json-file replacements.json
```

All three options are required and parsed as `pathlib.Path` values in a
shared `FileParserOptions` dataclass. Relative paths are relative to the
process working directory. Use `-h` or `--help` to display usage.
Missing required options, missing values, unknown options, and abbreviated
option names produce argparse diagnostics on stderr and exit status 2.
Help and valid parsing exit with status 0.

**This command currently parses arguments only.** It does not read or
validate source files, read JSON, or create output. A status of 0 does not
mean a batch file was generated. Stage 2 will pass the options dataclass
to the JSON file parser module for conversion.

The standalone script can be invoked by absolute path from outside the
repository. Use `uv run --project "$LTAW_TOP_LEVEL"` in that case to select
this project's managed environment.

## Requirements

- Python 3.14t+
