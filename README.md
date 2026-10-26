# lammps_trajectory_analysis_workspaces
This repository contains scripts, programs that aid in using the "lammp_trajectory_analysis_tools" on various computers.


## Quick Start
Setting up virtual environment for python >= 3.14
```
rm -rf ./.venv # Remove the old virtual environment
uv python install 3.14t # Install the free threaded python version
uv python pin 3.14t # Lock the python version.
uv run python -c "import sys; print('GIL Enabled:', sys._is_gil_enabled())" # Ensure the GIL is disabled.
```
## Documentation

## Requirements

- Python 3.14t+


