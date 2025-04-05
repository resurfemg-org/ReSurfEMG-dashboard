# ReSurfEMG-dashboard

Dashboard to use the ReSurfEMG library

[![DOI](https://zenodo.org/badge/516740721.svg)](https://zenodo.org/badge/latestdoi/516740721)

## Getting started

This dashboard requires that you have an environment with certain dependencies including dash. We recommend that you do the following:

    Install all Python packages required, using conda and the
    `environment.yml` file.
   * The commands for Windows users can be something like:
     `python -m venv .venv_dashboard`
     `.venv_dashboard\Scripts\active`
     `pip install -r requirements.txt`
   * Linux users can create their own environment by hand.

Once you have entered an environment with the necessary packages, run python index.py and a url for the dashboard should appear in your terminal (open the url). 
    `python index.py`.

## Building executable file

To ease the distribution and the use of the ReSurfEMG Dashboard, it is possible to build an executable file, through the following steps:

- Activate the virtual environment 
- Install the PyInstaller by running `pip install pyinstaller`
- Run `pyinstaller main.spec`

If the process is successful, the resurfemg_dashboard.exe file can be found in the /dist/main folder. By launching the executable file, the dashboard will be prompted. 

N.B. The dist folder containing the executable file should be created and uploaded when a new release of the dashboard is created.

## Linting work you want to add

Build the environment in the `environment_lint.yml` and enter it. You should then be able to use the `python setup.py lint` command. With care in the proper situation you may also use the `--fast` option. 