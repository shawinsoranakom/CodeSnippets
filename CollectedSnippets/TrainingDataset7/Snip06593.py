def remove_field(self, model, field):
        if isinstance(field, GeometryField) and field.spatial_index and not field.null:
            sql = self._delete_spatial_index_sql(model, field)
            try:
                self.execute(sql)
            except OperationalError:
                logger.error(
                    "Couldn't remove spatial index: %s (may be expected "
                    "if your storage engine doesn't support them).",
                    sql,
                )

        super().remove_field(model, field)