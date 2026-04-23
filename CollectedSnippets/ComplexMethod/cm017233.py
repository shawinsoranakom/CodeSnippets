def remove_field(self, model, field):
        """
        Remove a field from a model. Usually involves deleting a column,
        but for M2Ms may involve deleting a table.
        """
        # M2M fields are a special case
        if field.many_to_many:
            # For implicit M2M tables, delete the auto-created table
            if field.remote_field.through._meta.auto_created:
                self.delete_model(field.remote_field.through)
            # For explicit "through" M2M fields, do nothing
        elif (
            # Primary keys, unique fields, indexed fields, and foreign keys are
            # not supported in ALTER TABLE DROP COLUMN.
            not field.primary_key
            and not field.unique
            and not field.db_index
            and not (field.remote_field and field.db_constraint)
        ):
            super().remove_field(model, field)
        # For everything else, remake.
        else:
            # It might not actually have a column behind it
            if field.db_parameters(connection=self.connection)["type"] is None:
                return
            self._remake_table(model, delete_field=field)