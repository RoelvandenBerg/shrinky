import logging
import os
import json

from osgeo import ogr
from pathlib import Path

from shrinky.parse_geopackage_validator import parse_geopackage_validator_result


logger = logging.getLogger(__name__)


def parse_explicit_records(explicit_records):
    explicit_records = explicit_records.split(";")

    explicit_record_parsed = {}
    for explicit_record in explicit_records:
        if ":" in explicit_record:
            explicit_record = explicit_record.split(":")
            table_name = explicit_record[0]
            id_list = explicit_record[1].split(",")
            explicit_record_parsed[table_name] = id_list

    return explicit_record_parsed


def resolve_id_list(table_name, out_ds, explicit_records):
    if explicit_records is not None and table_name in explicit_records:
        explicit_records = parse_explicit_records(explicit_records)
        return explicit_records[table_name]

    sql = f"SELECT cast(rowid AS INTEGER) AS row_id FROM {table_name} LIMIT 3;"
    id_list_result = out_ds.ExecuteSQL(sql)

    id_list = []
    if id_list_result is not None:
        id_list = [row_id for row_id, in id_list_result]

    out_ds.ReleaseResultSet(id_list_result)

    return id_list


def main(gpkg_path, validation_result_path, result_target="shrink"):
    table_ids = parse_geopackage_validator_result(validation_result_path)

    in_file = Path(gpkg_path)
    out_file = in_file.parent / result_target / in_file.name

    if out_file.exists():
        os.remove(str(out_file))

    if not out_file.parent.exists():
        os.mkdir(str(out_file.parent))

    logger.info("Shrinking geopackage")
    logger.info(f"in: {in_file}")
    logger.info(f"out: {out_file}")
    driver = ogr.GetDriverByName("GPKG")

    in_ds = driver.Open(str(in_file))
    out_ds = driver.CreateDataSource(str(out_file))

    for in_layer in in_ds:
        layer_name = in_layer.GetName()

        # make a new layer with the same definition as the old one
        out_layer = out_ds.CreateLayer(
            layer_name,
            in_layer.GetSpatialRef(),
            geom_type=in_layer.GetGeomType(),
            options=[
                f'GEOMETRY_NAME={in_layer.GetGeometryColumn()}',
                'OVERWRITE=YES',
                f'FID={in_layer.GetFIDColumn()}'
            ]
        )

        layer_definition = in_layer.GetLayerDefn()
        for i in range(layer_definition.GetFieldCount()):
            field_definition = layer_definition.GetFieldDefn(i)
            out_layer.CreateField(field_definition)

        layer_ids = {int(x) for x in table_ids.get(layer_name, set())}
        for i in range(1, 7):
            if i not in layer_ids:
                layer_ids.add(i)
                break

        for feature_id in layer_ids:
            feature = in_layer.GetFeature(int(feature_id))
            if feature:
                out_layer.CreateFeature(feature)
            else:
                logger.warning(f"Warning, missing feature id: {layer_name} {feature_id} for file {gpkg_path}")

    logger.info(f'Shrinked {in_file.name} at {str(out_file)}')
