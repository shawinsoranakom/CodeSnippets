def get_geometry_type(self, table_name, description):
        """
        The geometry type OID used by PostGIS does not indicate the particular
        type of field that a geometry column is (e.g., whether it's a
        PointField or a PolygonField). Thus, this routine queries the PostGIS
        metadata tables to determine the geometry type.
        """
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT t.coord_dimension, t.srid, t.type FROM (
                    SELECT * FROM geometry_columns
                    UNION ALL
                    SELECT * FROM geography_columns
                ) AS t WHERE t.f_table_name = %s AND t.f_geometry_column = %s
            """,
                (table_name, description.name),
            )
            row = cursor.fetchone()
            if not row:
                raise Exception(
                    'Could not find a geometry or geography column for "%s"."%s"'
                    % (table_name, description.name)
                )
            dim, srid, field_type = row
            # OGRGeomType does not require GDAL and makes it easy to convert
            # from OGC geom type name to Django field.
            field_type = OGRGeomType(field_type).django
            # Getting any GeometryField keyword arguments that are not the
            # default.
            field_params = {}
            if self.postgis_oid_lookup.get(description.type_code) == "geography":
                field_params["geography"] = True
            if srid != 4326:
                field_params["srid"] = srid
            if dim != 2:
                field_params["dim"] = dim
        return field_type, field_params