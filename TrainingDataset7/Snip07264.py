def from_gml(cls, gml_string):
        return gdal.OGRGeometry.from_gml(gml_string).geos