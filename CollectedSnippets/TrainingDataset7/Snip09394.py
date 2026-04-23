def _alter_many_to_many(self, model, old_field, new_field, strict):
        """Alter M2Ms to repoint their to= endpoints."""
        # Rename the through table
        if (
            old_field.remote_field.through._meta.db_table
            != new_field.remote_field.through._meta.db_table
        ):
            self.alter_db_table(
                old_field.remote_field.through,
                old_field.remote_field.through._meta.db_table,
                new_field.remote_field.through._meta.db_table,
            )
        # Repoint the FK to the other side
        self.alter_field(
            new_field.remote_field.through,
            # The field that points to the target model is needed, so we can
            # tell alter_field to change it - this is m2m_reverse_field_name()
            # (as opposed to m2m_field_name(), which points to our model).
            old_field.remote_field.through._meta.get_field(
                old_field.m2m_reverse_field_name()
            ),
            new_field.remote_field.through._meta.get_field(
                new_field.m2m_reverse_field_name()
            ),
        )
        self.alter_field(
            new_field.remote_field.through,
            # for self-referential models we need to alter field from the other
            # end too
            old_field.remote_field.through._meta.get_field(old_field.m2m_field_name()),
            new_field.remote_field.through._meta.get_field(new_field.m2m_field_name()),
        )