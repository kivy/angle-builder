import argparse
import logging
import os
import sys

from angle_builder import __version__
from angle_builder.depot_tools import DepotTools
from angle_builder.storage import StorageFolderManager
from angle_builder.angle import ANGLE

__author__ = "Kivy Team and other contributors"
__copyright__ = "Kivy Team and other contributors"
__license__ = "MIT"

logging.basicConfig(level=logging.NOTSET)


def parse_args(args):
    """Parse command line parameters

    Args:
      args (List[str]): command line parameters as list of strings
          (for example  ``["--help"]``).

    Returns:
      :obj:`argparse.Namespace`: command line parameters namespace
    """
    parser = argparse.ArgumentParser(description="ANGLE builder CLI")

    parser.add_argument(
        dest="output_artifact_mode",
        help="Output artifact mode",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"angle-builder {__version__}",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        dest="loglevel",
        help="set loglevel to INFO",
        action="store_const",
        const=logging.INFO,
    )
    parser.add_argument(
        "-vv",
        "--very-verbose",
        dest="loglevel",
        help="set loglevel to DEBUG",
        action="store_const",
        const=logging.DEBUG,
    )
    parser.add_argument(
        "--branch",
        dest="branch",
        help="ANGLE branch to build",
        default="chromium/6261",
    )
    parser.add_argument(
        "--storage-folder",
        dest="storage_folder",
        help="Storage folder for ANGLE build",
        default=None,
    )
    parser.add_argument(
        "--artifact-output-folder",
        dest="artifact_output_folder",
        help="Output folder for artifacts",
        default=None,
    )

    parser.set_defaults(loglevel=logging.INFO)

    return parser.parse_args(args)


def main(args):
    """
    Args:
      args (List[str]): command line parameters as list of strings
          (for example  ``["--verbose", "42"]``).
    """
    args = parse_args(args)

    if args.artifact_output_folder is None:
        args.artifact_output_folder = os.path.join(
            os.getcwd(), "angle-artifacts"
        )

    storage_manager = StorageFolderManager(
        user_path=args.storage_folder,
        logger_level=args.loglevel,
    )
    storage_manager.ensure_folder()

    depot_tools = DepotTools(
        storage_manager=storage_manager, logger_level=args.loglevel
    )
    depot_tools.ensure_depot_tools()

    angle = ANGLE(
        branch=args.branch,
        storage_manager=storage_manager,
        logger_level=args.loglevel,
    )
    angle.build(
        output_artifact_mode=args.output_artifact_mode,
        output_folder=args.artifact_output_folder,
    )


def run():
    """Calls :func:`main` passing the CLI arguments extracted from :obj:`sys.argv`

    This function can be used as entry point to create console scripts with setuptools.
    """
    main(sys.argv[1:])


if __name__ == "__main__":
    run()
