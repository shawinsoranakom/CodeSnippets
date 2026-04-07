def _field_indexes_sql(self, model, field):
        if isinstance(field, GeometryField) and field.spatial_index and not field.null:
            with self.connection.cursor() as cursor:
                supports_spatial_index = (
                    self.connection.introspection.supports_spatial_index(
                        cursor, model._meta.db_table
                    )
                )
            sql = self._create_spatial_index_sql(model, field)
            if supports_spatial_index:
                return [sql]
            else:
                logger.error(
                    f"Cannot create SPATIAL INDEX {sql}. Only MyISAM, Aria, and InnoDB "
                    f"support them.",
                )
                return []
        return super()._field_indexes_sql(model, field)