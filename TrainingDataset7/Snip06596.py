def _create_spatial_index_sql(self, model, field):
        index_name = self._create_spatial_index_name(model, field)
        qn = self.connection.ops.quote_name
        return self.sql_add_spatial_index % {
            "index": qn(index_name),
            "table": qn(model._meta.db_table),
            "column": qn(field.column),
        }