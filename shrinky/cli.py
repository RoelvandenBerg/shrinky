# -*- coding: utf-8 -*-
"""CLI interface for shrinky"""
import logging
import sys

import click
import click_log

# Setup logging before package imports.
from shrinky.parse_geopackage_validator import parse_geopackage_validator_results

logger = logging.getLogger(__name__)
click_log.basic_config(logger)

from shrinky.core import main
from shrinky.error import AppError


@click.group()
def cli():
    pass


@cli.command(name="shrink")
@click.option(
    "-p",
    "--gpkg-path",
    required=True,
    default=None,
    help="Path pointing to the geopackage.gpkg file",
    type=click.types.Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        writable=False,
        allow_dash=False,
    ),
)
@click.option(
    "-v",
    "--validation-result-path",
    required=True,
    default=None,
    help="Path pointing to the result of a validation",
    type=click.types.Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        writable=False,
        allow_dash=False,
    ),
)
@click.option(
    "-t",
    "--result-target",
    required=False,
    default="shrink",
    help="Folder name where to place shrunken geopackage",
)
@click_log.simple_verbosity_option(logger)
def shrinky_command(gpkg_path, validation_result_path, result_target):
    """
    Shrink geopackage to minimal size. Shrinky picks random records to keep, or you can set these explicitly per table.
    """
    try:
        main(gpkg_path, validation_result_path, result_target)
    except AppError:
        logger.exception("shrinky failed:")
        sys.exit(1)


@cli.command(name="parse_validation_result")
@click.option(
    "-r",
    "--validation-result-path",
    required=True,
    default=None,
    help="Path pointing to the geopackage validation result file in json format",
    type=click.types.Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        writable=False,
        allow_dash=False,
    ),
)
@click_log.simple_verbosity_option(logger)
def parse_geopackage_validator_results_command(validation_result_path):
    """
    Shrink geopackage to minimal size. Shrinky picks random records to keep, or you can set these explicitly per table.
    """
    try:
        parse_geopackage_validator_results(validation_result_path)
    except AppError:
        logger.exception("shrinky failed:")
        sys.exit(1)


if __name__ == "__main__":
    cli()
