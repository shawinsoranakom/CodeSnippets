def get_geometry_type(self, table_name, description):
        with self.connection.cursor() as cursor:
            # In order to get the specific geometry type of the field,
            # we introspect on the table definition using `DESCRIBE`.
            cursor.execute("DESCRIBE %s" % self.connection.ops.quote_name(table_name))
            # Increment over description info until we get to the geometry
            # column.
            for column, typ, null, key, default, extra in cursor.fetchall():
                if column == description.name:
                    # Using OGRGeomType to convert from OGC name to Django
                    # field. MySQL does not support 3D or SRIDs, so the field
                    # params are empty.
                    field_type = OGRGeomType(typ).django
                    field_params = {}
                    break
        return field_type, field_params