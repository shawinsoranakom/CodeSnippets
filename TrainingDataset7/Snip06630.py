def delete_model(self, model):
        super().delete_model(model)
        self.execute(
            self.sql_clear_geometry_table_metadata
            % {
                "table": self.geo_quote_name(model._meta.db_table),
            }
        )