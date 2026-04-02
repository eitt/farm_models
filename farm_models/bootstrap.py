"""Runtime bootstrap helpers for dependency installation and pipeline launch."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def requirements_file() -> Path:
    """Return the repository requirements file path."""
    return Path(__file__).resolve().parent.parent / "requirements.txt"


def install_requirements(upgrade: bool = False) -> None:
    """Install or update the project requirements with the active Python interpreter."""
    req_path = requirements_file()
    if not req_path.exists():
        raise FileNotFoundError(f"Could not find requirements file at {req_path}")

    command = [sys.executable, "-m", "pip", "install", "-r", str(req_path)]
    if upgrade:
        command.insert(4, "--upgrade")

    print("Checking and installing required packages...")
    subprocess.run(command, check=True)


def build_bootstrap_parser() -> argparse.ArgumentParser:
    """Parse bootstrap-only arguments before handing control to the main pipeline."""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "--no-bootstrap",
        action="store_true",
        help="Skip automatic dependency installation before running the pipeline.",
    )
    parser.add_argument(
        "--upgrade-deps",
        action="store_true",
        help="Force pip to upgrade packages while installing the project requirements.",
    )
    return parser


def bootstrap_and_run(argv: list[str] | None = None) -> int:
    """Install requirements if needed and then launch the pipeline CLI."""
    parser = build_bootstrap_parser()
    bootstrap_args, remaining_args = parser.parse_known_args(argv)

    if not bootstrap_args.no_bootstrap:
        install_requirements(upgrade=bootstrap_args.upgrade_deps)

    from farm_models.pipeline import main as pipeline_main

    return pipeline_main(remaining_args)
