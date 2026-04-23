def get_geometry_type(self, table_name, description):
        with self.connection.cursor() as cursor:
            # Querying the `geometry_columns` table to get additional metadata.
            cursor.execute(
                "SELECT coord_dimension, srid, geometry_type "
                "FROM geometry_columns "
                "WHERE f_table_name=%s AND f_geometry_column=%s",
                (table_name, description.name),
            )
            row = cursor.fetchone()
            if not row:
                raise Exception(
                    'Could not find a geometry column for "%s"."%s"'
                    % (table_name, description.name)
                )

            # OGRGeomType does not require GDAL and makes it easy to convert
            # from OGC geom type name to Django field.
            ogr_type = row[2]
            if isinstance(ogr_type, int) and ogr_type > 1000:
                # SpatiaLite uses SFSQL 1.2 offsets 1000 (Z), 2000 (M), and
                # 3000 (ZM) to indicate the presence of higher dimensional
                # coordinates (M not yet supported by Django).
                ogr_type = ogr_type % 1000 + OGRGeomType.wkb25bit
            field_type = OGRGeomType(ogr_type).django

            # Getting any GeometryField keyword arguments that are not the
            # default.
            dim = row[0]
            srid = row[1]
            field_params = {}
            if srid != 4326:
                field_params["srid"] = srid
            if (isinstance(dim, str) and "Z" in dim) or dim == 3:
                field_params["dim"] = 3
        return field_type, field_params