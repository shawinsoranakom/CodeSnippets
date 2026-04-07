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
            strict,
        )
        # Added an index? Create any PostgreSQL-specific indexes.
        if (
            (not (old_field.db_index or old_field.unique) and new_field.db_index)
            or (not old_field.unique and new_field.unique)
            or (
                self._is_changing_type_of_indexed_text_column(
                    old_field, old_type, new_type
                )
            )
        ):
            like_index_statement = self._create_like_index_sql(model, new_field)
            if like_index_statement is not None:
                self.execute(like_index_statement)

        # Removed an index? Drop any PostgreSQL-specific indexes.
        if old_field.unique and not (new_field.db_index or new_field.unique):
            index_to_remove = self._create_index_name(
                model._meta.db_table, [old_field.column], suffix="_like"
            )
            self.execute(self._delete_index_sql(model, index_to_remove))