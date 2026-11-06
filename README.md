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

### Generate a Slurm Batch File

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
Help and successful conversion exit with status 0. Conversion failures
produce a concise stderr diagnostic and exit status 1.

For example, a template containing:

```text
#!/bin/bash
#SBATCH --job-name=__JOB_NAME__
#SBATCH --time=__WALLTIME__
echo "__JOB_NAME__"
```

with this JSON replacement map:

```json
{
  "__JOB_NAME__": "analysis",
  "__WALLTIME__": "01:00:00"
}
```

produces:

```text
#!/bin/bash
#SBATCH --job-name=analysis
#SBATCH --time=01:00:00
echo "analysis"
```

JSON must be an object whose keys fully match the placeholder pattern
`__(.*?)__` (without DOTALL) and whose values are strings. Missing
replacements are errors; unused keys are allowed. Substitution is literal,
single-pass, and non-recursive, with no shell expansion or job submission.

The script passes the parsed dataclass directly to
`json_file_parser.create_output_file(options)`. Sources are read as UTF-8;
line endings and final-newline presence are preserved. Validation and
encoding finish before output is created. Existing output entries,
including symlinks, are never overwritten, and the output parent directory
must already exist. Failed writes remove incomplete output; cleanup
failures are reported explicitly. Success produces no console output.

The standalone script can be invoked by absolute path from outside the
repository. Use `uv run --project "$LTAW_TOP_LEVEL"` in that case to select
this project's managed environment.

## Requirements

- Python 3.14t+
