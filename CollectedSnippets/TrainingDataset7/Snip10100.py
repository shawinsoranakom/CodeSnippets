def generate_altered_fields(self):
        """
        Make AlterField operations, or possibly RemovedField/AddField if alter
        isn't possible.
        """
        for app_label, model_name, field_name in sorted(
            self.old_field_keys & self.new_field_keys
        ):
            # Did the field change?
            old_model_name = self.renamed_models.get(
                (app_label, model_name), model_name
            )
            old_field_name = self.renamed_fields.get(
                (app_label, model_name, field_name), field_name
            )
            old_field = self.from_state.models[app_label, old_model_name].get_field(
                old_field_name
            )
            new_field = self.to_state.models[app_label, model_name].get_field(
                field_name
            )
            dependencies = []
            # Implement any model renames on relations; these are handled by
            # RenameModel so we need to exclude them from the comparison
            if hasattr(new_field, "remote_field") and getattr(
                new_field.remote_field, "model", None
            ):
                rename_key = resolve_relation(
                    new_field.remote_field.model, app_label, model_name
                )
                if rename_key in self.renamed_models:
                    new_field.remote_field.model = old_field.remote_field.model
                # Handle ForeignKey which can only have a single to_field.
                remote_field_name = getattr(new_field.remote_field, "field_name", None)
                if remote_field_name:
                    to_field_rename_key = (*rename_key, remote_field_name)
                    if to_field_rename_key in self.renamed_fields:
                        # Repoint both model and field name because to_field
                        # inclusion in ForeignKey.deconstruct() is based on
                        # both.
                        new_field.remote_field.model = old_field.remote_field.model
                        new_field.remote_field.field_name = (
                            old_field.remote_field.field_name
                        )
                # Handle ForeignObjects which can have multiple
                # from_fields/to_fields.
                from_fields = getattr(new_field, "from_fields", None)
                if from_fields:
                    from_rename_key = (app_label, model_name)
                    new_field.from_fields = tuple(
                        [
                            self.renamed_fields.get(
                                (*from_rename_key, from_field), from_field
                            )
                            for from_field in from_fields
                        ]
                    )
                    new_field.to_fields = tuple(
                        [
                            self.renamed_fields.get((*rename_key, to_field), to_field)
                            for to_field in new_field.to_fields
                        ]
                    )
                    if old_from_fields := getattr(old_field, "from_fields", None):
                        old_field.from_fields = tuple(old_from_fields)
                        old_field.to_fields = tuple(old_field.to_fields)
                dependencies.extend(
                    self._get_dependencies_for_foreign_key(
                        app_label,
                        model_name,
                        new_field,
                        self.to_state,
                    )
                )
            if hasattr(new_field, "remote_field") and getattr(
                new_field.remote_field, "through", None
            ):
                rename_key = resolve_relation(
                    new_field.remote_field.through, app_label, model_name
                )
                if rename_key in self.renamed_models:
                    new_field.remote_field.through = old_field.remote_field.through
            old_field_dec = self.deep_deconstruct(old_field)
            new_field_dec = self.deep_deconstruct(new_field)
            # If the field was confirmed to be renamed it means that only
            # db_column was allowed to change which generate_renamed_fields()
            # already accounts for by adding an AlterField operation.
            if old_field_dec != new_field_dec and old_field_name == field_name:
                both_m2m = old_field.many_to_many and new_field.many_to_many
                neither_m2m = not old_field.many_to_many and not new_field.many_to_many
                target_changed = (
                    both_m2m and new_field_dec[2]["to"] != old_field_dec[2]["to"]
                )
                if (both_m2m or neither_m2m) and not target_changed:
                    # Either both fields are m2m or neither is
                    preserve_default = True
                    if (
                        old_field.null
                        and not new_field.null
                        and not new_field.has_default()
                        and not new_field.has_db_default()
                        and not new_field.many_to_many
                    ):
                        field = new_field.clone()
                        new_default = self.questioner.ask_not_null_alteration(
                            field_name, model_name
                        )
                        if new_default is not models.NOT_PROVIDED:
                            field.default = new_default
                            preserve_default = False
                    else:
                        field = new_field
                    self.add_operation(
                        app_label,
                        operations.AlterField(
                            model_name=model_name,
                            name=field_name,
                            field=field,
                            preserve_default=preserve_default,
                        ),
                        dependencies=dependencies,
                    )
                else:
                    # We cannot alter between m2m and concrete fields
                    self._generate_removed_field(app_label, model_name, field_name)
                    self._generate_added_field(app_label, model_name, field_name)