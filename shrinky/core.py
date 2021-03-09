import logging
import os

from osgeo import ogr
from pathlib import Path

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


def main(gpkg_path, explicit_records, result_target="shrink"):

    in_file = Path(gpkg_path)
    out_file = in_file.parent / result_target / in_file.name

    if not out_file.parent.exists():
        os.mkdir(result_target)

    print("Shrink geopackage")
    print(f"in: {in_file}")
    print(f"out: {out_file}")

    in_ds = ogr.GetDriverByName("GPKG").Open(str(in_file))
    out_ds = ogr.GetDriverByName("GPKG").CopyDataSource(in_ds, str(out_file))

    geo_tables = out_ds.ExecuteSQL("SELECT table_name FROM gpkg_geometry_columns;")

    for (table_name,) in geo_tables:

        id_list = resolve_id_list(table_name, in_ds, explicit_records)
        id_list = "'" + "', '".join(map(str, id_list)) + "'"

        sql = f"DELETE FROM {table_name} WHERE rowid NOT IN({id_list});"
        delete = out_ds.ExecuteSQL(sql)
        out_ds.ReleaseResultSet(delete)

    out_ds.ReleaseResultSet(geo_tables)
    print('Shrinkaded!')
