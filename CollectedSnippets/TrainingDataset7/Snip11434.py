def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        del kwargs["to_fields"]
        del kwargs["from_fields"]
        # Handle the simpler arguments
        if self.db_index:
            del kwargs["db_index"]
        else:
            kwargs["db_index"] = False
        if self.db_constraint is not True:
            kwargs["db_constraint"] = self.db_constraint
        # Rel needs more work.
        to_meta = getattr(self.remote_field.model, "_meta", None)
        if self.remote_field.field_name and (
            not to_meta
            or (to_meta.pk and self.remote_field.field_name != to_meta.pk.name)
        ):
            kwargs["to_field"] = self.remote_field.field_name
        return name, path, args, kwargs