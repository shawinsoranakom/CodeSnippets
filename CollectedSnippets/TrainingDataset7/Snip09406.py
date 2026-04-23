def _field_should_be_altered(self, old_field, new_field, ignore=None):
        if (not (old_field.concrete or old_field.many_to_many)) and (
            not (new_field.concrete or new_field.many_to_many)
        ):
            return False
        ignore = ignore or set()
        _, old_path, old_args, old_kwargs = old_field.deconstruct()
        _, new_path, new_args, new_kwargs = new_field.deconstruct()
        # Don't alter when:
        # - changing only a field name (unless it's a many-to-many)
        # - changing an attribute that doesn't affect the schema
        # - changing an attribute in the provided set of ignored attributes
        # - adding only a db_column and the column name is not changed
        # - db_table does not change for model referenced by foreign keys
        for attr in ignore.union(old_field.non_db_attrs):
            old_kwargs.pop(attr, None)
        for attr in ignore.union(new_field.non_db_attrs):
            new_kwargs.pop(attr, None)
        if (
            not new_field.many_to_many
            and old_field.remote_field
            and new_field.remote_field
            and old_field.remote_field.model._meta.db_table
            == new_field.remote_field.model._meta.db_table
        ):
            old_kwargs.pop("to", None)
            new_kwargs.pop("to", None)
        # db_default can take many forms but result in the same SQL.
        if (
            old_kwargs.get("db_default")
            and new_kwargs.get("db_default")
            and self.db_default_sql(old_field) == self.db_default_sql(new_field)
        ):
            old_kwargs.pop("db_default")
            new_kwargs.pop("db_default")
        if (
            old_field.concrete
            and new_field.concrete
            and (self.quote_name(old_field.column) != self.quote_name(new_field.column))
        ):
            return True
        if (
            old_field.many_to_many
            and new_field.many_to_many
            and old_field.name != new_field.name
        ):
            return True
        return (old_path, old_args, old_kwargs) != (new_path, new_args, new_kwargs)