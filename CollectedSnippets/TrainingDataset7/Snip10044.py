def _alter_many_to_many(self, model, old_field, new_field, strict):
        """Alter M2Ms to repoint their to= endpoints."""
        if (
            old_field.remote_field.through._meta.db_table
            == new_field.remote_field.through._meta.db_table
        ):
            # The field name didn't change, but some options did, so we have to
            # propagate this altering.
            self._remake_table(
                old_field.remote_field.through,
                alter_fields=[
                    (
                        # The field that points to the target model is needed,
                        # so that table can be remade with the new m2m field -
                        # this is m2m_reverse_field_name().
                        old_field.remote_field.through._meta.get_field(
                            old_field.m2m_reverse_field_name()
                        ),
                        new_field.remote_field.through._meta.get_field(
                            new_field.m2m_reverse_field_name()
                        ),
                    ),
                    (
                        # The field that points to the model itself is needed,
                        # so that table can be remade with the new self field -
                        # this is m2m_field_name().
                        old_field.remote_field.through._meta.get_field(
                            old_field.m2m_field_name()
                        ),
                        new_field.remote_field.through._meta.get_field(
                            new_field.m2m_field_name()
                        ),
                    ),
                ],
            )
            return

        # Make a new through table
        self.create_model(new_field.remote_field.through)
        # Copy the data across
        self.execute(
            "INSERT INTO %s (%s) SELECT %s FROM %s"
            % (
                self.quote_name(new_field.remote_field.through._meta.db_table),
                ", ".join(
                    [
                        "id",
                        new_field.m2m_column_name(),
                        new_field.m2m_reverse_name(),
                    ]
                ),
                ", ".join(
                    [
                        "id",
                        old_field.m2m_column_name(),
                        old_field.m2m_reverse_name(),
                    ]
                ),
                self.quote_name(old_field.remote_field.through._meta.db_table),
            )
        )
        # Delete the old through table
        self.delete_model(old_field.remote_field.through)