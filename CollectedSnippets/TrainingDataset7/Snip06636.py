def _create_spatial_index_sql(self, model, field):
        index_name = self._create_spatial_index_name(model, field)
        return self.sql_add_spatial_index % {
            "index": self.quote_name(index_name),
            "table": self.quote_name(model._meta.db_table),
            "column": self.quote_name(field.column),
        }