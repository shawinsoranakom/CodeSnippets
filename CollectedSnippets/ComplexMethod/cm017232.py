def add_field(self, model, field):
        """Create a field on a model."""
        from django.db.models.expressions import Value

        # Special-case implicit M2M tables.
        if field.many_to_many and field.remote_field.through._meta.auto_created:
            self.create_model(field.remote_field.through)
        elif isinstance(field, CompositePrimaryKey):
            # If a CompositePrimaryKey field was added, the existing primary
            # key field had to be altered too, resulting in an AddField,
            # AlterField migration. The table cannot be re-created on AddField,
            # it would result in a duplicate primary key error.
            return
        elif (
            # Primary keys and unique fields are not supported in ALTER TABLE
            # ADD COLUMN.
            field.primary_key
            or field.unique
            or not field.null
            # Fields with default values cannot by handled by ALTER TABLE ADD
            # COLUMN statement because DROP DEFAULT is not supported in
            # ALTER TABLE.
            or self.effective_default(field) is not None
            # Fields with non-constant defaults cannot by handled by ALTER
            # TABLE ADD COLUMN statement.
            or (field.has_db_default() and not isinstance(field.db_default, Value))
        ):
            self._remake_table(model, create_field=field)
        else:
            super().add_field(model, field)