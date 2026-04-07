def remove_field(self, model, field):
        if isinstance(field, GeometryField):
            self.execute(
                self.sql_clear_geometry_field_metadata
                % {
                    "table": self.geo_quote_name(model._meta.db_table),
                    "column": self.geo_quote_name(field.column),
                }
            )
            if field.spatial_index:
                self.execute(self._delete_spatial_index_sql(model, field))
        super().remove_field(model, field)