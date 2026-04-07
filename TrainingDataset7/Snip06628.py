def column_sql(self, model, field, include_default=False):
        column_sql = super().column_sql(model, field, include_default)
        if isinstance(field, GeometryField):
            self.geometry_sql.append(
                self.sql_add_geometry_metadata
                % {
                    "table": self.geo_quote_name(model._meta.db_table),
                    "column": self.geo_quote_name(field.column),
                    "dim0": field._extent[0],
                    "dim1": field._extent[1],
                    "dim2": field._extent[2],
                    "dim3": field._extent[3],
                    "tolerance": field._tolerance,
                    "srid": field.srid,
                }
            )
        return column_sql