# -*- coding: utf-8 -*-
"""CLI interface for shrinky"""
import logging

import click
import click_log

logger = logging.getLogger(__name__)
click_log.basic_config(logger)

from shrinky.core import main

logger.info("info logging")

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
    "-t",
    "--result-target",
    required=False,
    default="shrink",
    help="Folder name where to place shrunken geopackage",
)
@click.option(
    "-s",
    "--simplify-threshold",
    required=False,
    default=107.52,
    type=click.types.FLOAT,
    help="Simplify-threshold (hint: take the fourfold based on zoomlevel for RD (from 0): [3440.640, 1720.320, 860.160, 430.080, 215.040, 107.520, 53.760, 26.880, 13.440, 6.720, 3.360, 1.680, 0.840, 0.420, 0.210, 0.105])",
)
@click.option(
    "-b",
    "--bbox-filter",
    required=False,
    default="",
    type=click.types.STRING,
    help="BBOX in the same CRS as the source, from which geoms for each layer are preferred. Example: 121088.7989104228764,486719.8953262089635,121578.3960113508656,487207.117663510784"
)
@click_log.simple_verbosity_option(logger)
def shrinky_command(gpkg_path, result_target, simplify_threshold, bbox_filter):
    """
    Shrink geopackage to minimal size. Shrinky picks random records to keep, or you can set these explicitly per table.
    """
    main(gpkg_path, result_target, simplify_threshold, bbox_filter, logger)


if __name__ == "__main__":
    cli()
