def _alter_field(
        self,
        model,
        old_field,
        new_field,
        old_type,
        new_type,
        old_db_params,
        new_db_params,
        strict=False,
    ):
        super()._alter_field(
            model,
            old_field,
            new_field,
            old_type,
            new_type,
            old_db_params,
            new_db_params,
            strict=strict,
        )

        old_field_spatial_index = (
            isinstance(old_field, GeometryField)
            and old_field.spatial_index
            and not old_field.null
        )
        new_field_spatial_index = (
            isinstance(new_field, GeometryField)
            and new_field.spatial_index
            and not new_field.null
        )
        if not old_field_spatial_index and new_field_spatial_index:
            self.execute(self._create_spatial_index_sql(model, new_field))
        elif old_field_spatial_index and not new_field_spatial_index:
            self.execute(self._delete_spatial_index_sql(model, old_field))