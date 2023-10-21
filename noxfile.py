import nox
import os
import sys
from pathlib import Path


# Options to modify nox behaviour
nox.options.reuse_existing_virtualenvs = True
if sys.platform == "linux":
    nox.options.sessions = ["pre-commit", "pybamm-requires", "unit"]
else:
    nox.options.sessions = ["pre-commit", "unit"]


homedir = os.getenv("HOME")
PYBAMM_ENV = {
    "SUNDIALS_INST": f"{homedir}/.local",
    "LD_LIBRARY_PATH": f"{homedir}/.local/lib:",
}
VENV_DIR = Path('./venv').resolve()


def set_environment_variables(env_dict, session):
    """
    Sets environment variables for a nox session object.

    Parameters
    -----------
        session : nox.Session
            The session to set the environment variables for.
        env_dict : dict
            A dictionary of environment variable names and values.

    """
    for key, value in env_dict.items():
        session.env[key] = value


@nox.session(name="pybamm-requires")
def run_pybamm_requires(session):
    """Download, compile, and install the build-time requirements for Linux and macOS: the SuiteSparse and SUNDIALS libraries."""  # noqa: E501
    set_environment_variables(PYBAMM_ENV, session=session)
    force_rebuild = "--force" in session.posargs
    sundials_so_path = [
            Path("/path/to/sundials/libsundials_idas.so"),
            Path("/path/to/sundials/libsundials_idas.dylib"),

            Path("/path/to/sundials/libsundials_sunlinsolklu.so"),
            Path("/path/to/sundials/libsundials_sunlinsolklu.dylib"),

            Path("/path/to/sundials/libsundials_sunlinsoldense.so"),
            Path("/path/to/sundials/libsundials_sunlinsoldense.dylib"),

            Path("/path/to/sundials/libsundials_sunlinsolspbcgs.so"),
            Path("/path/to/sundials/libsundials_sunlinsolspbcgs.dylib"),

            Path("/path/to/sundials/libsundials_sunlinsollapackdense.so"),
            Path("/path/to/sundials/libsundials_sunlinsollapackdense.dylib"),

            Path("/path/to/sundials/libsundials_sunmatrixsparse.so"),
            Path("/path/to/sundials/libsundials_sunmatrixsparse.dylib"),

            Path("/path/to/sundials/libsundials_nvecserial.so"),
            Path("/path/to/sundials/libsundials_nvecserial.dylib"),

            Path("/path/to/sundials/libsundials_nvecopenmp.so"),
            Path("/path/to/sundials/libsundials_nvecopenmp.dylib")
        ]
    klu_so_path = [
            Path("/path/to/suitesparse/libsuitesparseconfig.so"),
            Path("/path/to/suitesparse/libsuitesparseconfig.dylib"), # for MacOS

            Path("/path/to/suitesparse/libklu.so"),
            Path("/path/to/suitesparse/libklu.dylib"),

            Path("/path/to/suitesparse/libamd.so"),
            Path("/path/to/suitesparse/libamd.dylib"),

            Path("/path/to/suitesparse/libcolamd.so"),
            Path("/path/to/suitesparse/libcolamd.dylib"),

            Path("/path/to/suitesparse/libbtf.so"),
            Path("/path/to/suitesparse/libbtf.dylib"),
        ]
    if sys.platform != "win32":
        session.install("wget", "cmake", silent=False)

        if (sundials_so_path.exists() and
            klu_so_path.exists()) and not force_rebuild:
            session.warn("Found existing build-time requirements, skipping installation. Note: run with the --force flag (nox -s pybamm-requires -- --force) to invoke re-installation.")  # noqa: E501
            return
            session.run("python", "scripts/install_Klu_Sundials.py")
        elif os.path.exists("./pybind11"):
            session.log("Found pybind11")
            return
            session.run(
                "git",
                "clone",
                "https://github.com/pybind/pybind11.git",
                "pybind11/",
                external=True,
            )
    else:
        session.error("nox -s pybamm-requires is only available on Linux & macOS.")


@nox.session(name="coverage")
def run_coverage(session):
    """Run the coverage tests and generate an XML report."""
    set_environment_variables(PYBAMM_ENV, session=session)
    session.install("coverage", silent=False)
    session.install("-e", ".[all]", silent=False)
    if sys.platform != "win32":
        session.install("-e", ".[odes]", silent=False)
        session.install("-e", ".[jax]", silent=False)
    session.run("coverage", "run", "--rcfile=.coveragerc", "run-tests.py", "--nosub")
    session.run("coverage", "combine")
    session.run("coverage", "xml")


@nox.session(name="integration")
def run_integration(session):
    """Run the integration tests."""
    set_environment_variables(PYBAMM_ENV, session=session)
    session.install("-e", ".[all]", silent=False)
    if sys.platform == "linux":
        session.install("-e", ".[odes]", silent=False)
    session.run("python", "run-tests.py", "--integration")


@nox.session(name="doctests")
def run_doctests(session):
    """Run the doctests and generate the output(s) in the docs/build/ directory."""
    session.install("-e", ".[all,docs]", silent=False)
    session.run("python", "run-tests.py", "--doctest")


@nox.session(name="unit")
def run_unit(session):
    """Run the unit tests."""
    set_environment_variables(PYBAMM_ENV, session=session)
    session.install("-e", ".[all]", silent=False)
    if sys.platform == "linux":
        session.install("-e", ".[odes]", silent=False)
        session.install("-e", ".[jax]", silent=False)
    session.run("python", "run-tests.py", "--unit")


@nox.session(name="examples")
def run_examples(session):
    """Run the examples tests for Jupyter notebooks."""
    set_environment_variables(PYBAMM_ENV, session=session)
    session.install("-e", ".[all,dev]", silent=False)
    notebooks_to_test = session.posargs if session.posargs else []
    session.run("pytest", "--nbmake", *notebooks_to_test, external=True)


@nox.session(name="scripts")
def run_scripts(session):
    """Run the scripts tests for Python scripts."""
    set_environment_variables(PYBAMM_ENV, session=session)
    session.install("-e", ".[all]", silent=False)
    session.run("python", "run-tests.py", "--scripts")


@nox.session(name="dev")
def set_dev(session):
    """Install PyBaMM in editable mode."""
    set_environment_variables(PYBAMM_ENV, session=session)
    session.install("virtualenv", "cmake")
    session.run("virtualenv", os.fsdecode(VENV_DIR), silent=True)
    python = os.fsdecode(VENV_DIR.joinpath("bin/python"))
    if sys.platform == "linux":
        session.run(python,
                    "-m",
                    "pip",
                    "install",
                    ".[all,dev,jax,odes]",
                    external=True,
        )
    else:
        session.run(python, "-m", "pip", "install", "-e", ".[all,dev]", external=True)


@nox.session(name="tests")
def run_tests(session):
    """Run the unit tests and integration tests sequentially."""
    set_environment_variables(PYBAMM_ENV, session=session)
    session.install("-e", ".[all]", silent=False)
    if sys.platform == "linux" or sys.platform == "darwin":
        session.install("-e", ".[odes]", silent=False)
        session.install("-e", ".[jax]", silent=False)
    session.run("python", "run-tests.py", "--all")


@nox.session(name="docs")
def build_docs(session):
    """Build the documentation and load it in a browser tab, rebuilding on changes."""
    envbindir = session.bin
    session.install("-e", ".[all,docs]", silent=False)
    session.chdir("docs")
    # Local development
    if session.interactive:
        session.run(
        "sphinx-autobuild",
        "-j",
        "auto",
        "--open-browser",
        "-qT",
        ".",
        f"{envbindir}/../tmp/html",
        )
    # Runs in CI only, treating warnings as errors
    else:
        session.run(
        "sphinx-build",
        "-j",
        "auto",
        "-b",
        "html",
        "-W",
        "--keep-going",
        ".",
        f"{envbindir}/../tmp/html",
        )


@nox.session(name="pre-commit")
def lint(session):
    """Check all files against the defined pre-commit hooks."""
    session.install("pre-commit", silent=False)
    session.run("pre-commit", "run", "--all-files")


@nox.session(name="quick", reuse_venv=True)
def run_quick(session):
    """Run integration tests, unit tests, and doctests sequentially"""
    run_tests(session)
    run_doctests(session)
