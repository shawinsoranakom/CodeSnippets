def rename_field(self, app_label, model_name, old_name, new_name):
        model_key = app_label, model_name
        model_state = self.models[model_key]
        # Rename the field.
        fields = model_state.fields
        try:
            found = fields.pop(old_name)
        except KeyError:
            raise FieldDoesNotExist(
                f"{app_label}.{model_name} has no field named '{old_name}'"
            )
        fields[new_name] = found
        for field in fields.values():
            # Fix from_fields to refer to the new field.
            from_fields = getattr(field, "from_fields", None)
            if from_fields:
                field.from_fields = tuple(
                    [
                        new_name if from_field_name == old_name else from_field_name
                        for from_field_name in from_fields
                    ]
                )
            # Fix field names (e.g. for CompositePrimaryKey) to refer to the
            # new field.
            if field_names := getattr(field, "field_names", None):
                if old_name in field_names:
                    field.field_names = tuple(
                        [
                            new_name if field_name == old_name else field_name
                            for field_name in field.field_names
                        ]
                    )
        # Fix index/unique_together to refer to the new field.
        options = model_state.options
        for option in ("index_together", "unique_together"):
            if option in options:
                options[option] = {
                    tuple(new_name if n == old_name else n for n in together)
                    for together in options[option]
                }
        # Fix to_fields to refer to the new field.
        delay = True
        references = get_references(self, model_key, (old_name, found))
        for *_, field, reference in references:
            delay = False
            if reference.to:
                remote_field, to_fields = reference.to
                if getattr(remote_field, "field_name", None) == old_name:
                    remote_field.field_name = new_name
                if to_fields:
                    field.to_fields = tuple(
                        [
                            new_name if to_field_name == old_name else to_field_name
                            for to_field_name in to_fields
                        ]
                    )
        if self._relations is not None:
            old_name_lower = old_name.lower()
            new_name_lower = new_name.lower()
            for to_model in self._relations.values():
                if old_name_lower in to_model[model_key]:
                    field = to_model[model_key].pop(old_name_lower)
                    field.name = new_name_lower
                    to_model[model_key][new_name_lower] = field
        self.reload_model(*model_key, delay=delay)