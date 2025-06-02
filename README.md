# ReSurfEMG-dashboard

Dashboard to use the ReSurfEMG library

[![DOI](https://zenodo.org/badge/516740721.svg)](https://zenodo.org/badge/latestdoi/516740721)

## Getting started

1) This dashboard requires that you have an environment with certain dependencies including dash. We recommend that you do the following:
   * For Windows users:
     ``` sh
     python -m venv .venv_dashboard
     .venv_dashboard\Scripts\active
     pip install resurfemg_dashboard
     ```

   * For Linux/OSx users:
     ``` sh 
     python3 -m venv .venv_dashboard
     source .venv_dashboard/bin/active
     python3 -m pip install resurfemg_dashboard
     ```

2) Once you have entered an environment with the necessary packages, run the resurfemg_dashboard module with Python and a url for the dashboard should appear in your terminal (open the url).
    ``` sh
    python -m resurfemg_dashboard
    ```
    (For Linux/OSc use: `python3`)

## Building executable file

To ease the distribution and the use of the ReSurfEMG Dashboard, it is possible to build an executable file, through the following steps:

- Activate the virtual environment 
- Install the PyInstaller by running
    ``` sh
    pip install pyinstaller
    ```
- Run
    ``` sh
    pyinstaller resurfemg_dashboard/main.spec
    ```

If the process is successful, the resurfemg_dashboard.exe file can be found in the /dist/main folder. By launching the executable file, the dashboard will be prompted. 

N.B. The dist folder containing the executable file should be created and uploaded when a new release of the dashboard is created.

## Testing

Linting tests are included in this project. Build the environment in the `pyproject.toml` and enter it. You should then be able to use the `python setup.py lint` command. With care in the proper situation you may also use the `--fast` option. 