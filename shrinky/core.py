import os
import logging

from osgeo import ogr
from pathlib import Path

LOGGER = logging.getLogger(__name__)


MULTI = {
    "MULTIPOINT": ogr.wkbMultiPoint,
    "MULTILINESTRING": ogr.wkbMultiLineString,
    "MULTIPOLYGON": ogr.wkbMultiPolygon,
}


def make_multi(feature, geom_type):
    multi_geom_type = MULTI.get(geom_type)
    if multi_geom_type is None:
        return feature
    multi_geom = ogr.Geometry(multi_geom_type)
    multi_geom.AddGeometry(feature)
    return multi_geom


def simplify_and_convert_multi_to_multi(feature, simplify_threshold):
    geom = feature.geometry()
    if geom.IsEmpty:
        return feature

    geometry_type = geom.GetGeometryName()

    simplified = geom.Simplify(simplify_threshold).MakeValid()
    if simplified.GetGeometryName() == geometry_type:
        feature.SetGeometry(simplified)
    elif MULTI.get(geometry_type):
        feature.SetGeometry(make_multi(simplified, geometry_type))
    else:
        raise ValueError(f"Expected: {simplified.GetGeometryName()} to be equal to {geometry_type} or to be a MULTI geometry of type {', '.join(MULTI.keys())}")
    return feature


def main(gpkg_path, result_target="shrink", simplify_threshold=107.52, bbox_filter="", logger=LOGGER):
    in_file = Path(gpkg_path)
    out_file = in_file.parent / result_target / in_file.name
    geom_filter = ogr.CreateGeometryFromWkt(wkt_polygon_from_bbox_string(bbox_filter, logger))

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

    for in_layer in (in_ds.GetLayer(i) for i in range(in_ds.GetLayerCount())):

        # make a new layer with the same definition as the old one
        out_layer = out_ds.CreateLayer(
            in_layer.GetName(),
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

        if in_layer.GetFeatureCount():

            feature = in_layer.GetNextFeature()
            if geom_filter:
                in_layer.SetSpatialFilter(geom_filter)
                new_feature = in_layer.GetNextFeature()
                if new_feature is not None:
                    feature = new_feature
            feature = simplify_and_convert_multi_to_multi(feature, simplify_threshold)

            out_layer.CreateFeature(feature)

    logger.info(f'Shrunk {in_file.name} at {str(out_file)}')


def wkt_polygon_from_bbox_string(bbox, logger):
    if not bbox:
        return ""
    wkt = wkt_polygon_from_bbox(*bbox.strip().split(','))
    logger.info("using wkt: %s", wkt)
    return wkt


def wkt_polygon_from_bbox(minx, miny, maxx, maxy):
    return f"POLYGON(({minx} {miny},{minx} {maxy},{maxx} {maxy},{maxx} {miny},{minx} {miny}))"
