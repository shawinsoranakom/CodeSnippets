def alter_db_table(self, model, old_db_table, new_db_table):
        from django.contrib.gis.db.models import GeometryField

        if old_db_table == new_db_table or (
            self.connection.features.ignores_table_name_case
            and old_db_table.lower() == new_db_table.lower()
        ):
            return
        # Remove geometry-ness from temp table
        for field in model._meta.local_fields:
            if isinstance(field, GeometryField):
                self.execute(
                    self.sql_remove_geometry_metadata
                    % {
                        "table": self.quote_name(old_db_table),
                        "column": self.quote_name(field.column),
                    }
                )
        # Alter table
        super().alter_db_table(model, old_db_table, new_db_table)
        # Repoint any straggler names
        for geom_table in self.geometry_tables:
            try:
                self.execute(
                    self.sql_update_geometry_columns
                    % {
                        "geom_table": geom_table,
                        "old_table": self.quote_name(old_db_table),
                        "new_table": self.quote_name(new_db_table),
                    }
                )
            except DatabaseError:
                pass
        # Re-add geometry-ness and rename spatial index tables
        for field in model._meta.local_fields:
            if isinstance(field, GeometryField):
                self.execute(
                    self.sql_recover_geometry_metadata
                    % {
                        "table": self.geo_quote_name(new_db_table),
                        "column": self.geo_quote_name(field.column),
                        "srid": field.srid,
                        "geom_type": self.geo_quote_name(field.geom_type),
                        "dim": field.dim,
                    }
                )
            if getattr(field, "spatial_index", False):
                self.execute(
                    self.sql_rename_table
                    % {
                        "old_table": self.quote_name(
                            "idx_%s_%s" % (old_db_table, field.column)
                        ),
                        "new_table": self.quote_name(
                            "idx_%s_%s" % (new_db_table, field.column)
                        ),
                    }
                )