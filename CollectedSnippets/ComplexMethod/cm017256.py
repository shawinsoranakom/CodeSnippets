def create_renamed_fields(self):
        """Work out renamed fields."""
        self.renamed_operations = []
        old_field_keys = self.old_field_keys.copy()
        for app_label, model_name, field_name in sorted(
            self.new_field_keys - old_field_keys
        ):
            old_model_name = self.renamed_models.get(
                (app_label, model_name), model_name
            )
            old_model_state = self.from_state.models[app_label, old_model_name]
            new_model_state = self.to_state.models[app_label, model_name]
            field = new_model_state.get_field(field_name)
            # Scan to see if this is actually a rename!
            field_dec = self.deep_deconstruct(field)
            for rem_app_label, rem_model_name, rem_field_name in sorted(
                old_field_keys - self.new_field_keys
            ):
                if rem_app_label == app_label and rem_model_name == model_name:
                    old_field = old_model_state.get_field(rem_field_name)
                    old_field_dec = self.deep_deconstruct(old_field)
                    if (
                        field.remote_field
                        and field.remote_field.model
                        and "to" in old_field_dec[2]
                    ):
                        old_rel_to = old_field_dec[2]["to"]
                        if old_rel_to in self.renamed_models_rel:
                            old_field_dec[2]["to"] = self.renamed_models_rel[old_rel_to]
                    old_field.set_attributes_from_name(rem_field_name)
                    old_db_column = old_field.get_attname_column()[1]
                    if old_field_dec == field_dec or (
                        # Was the field renamed and db_column equal to the
                        # old field's column added?
                        old_field_dec[0:2] == field_dec[0:2]
                        and dict(old_field_dec[2], db_column=old_db_column)
                        == field_dec[2]
                    ):
                        if self.questioner.ask_rename(
                            model_name, rem_field_name, field_name, field
                        ):
                            self.renamed_operations.append(
                                (
                                    rem_app_label,
                                    rem_model_name,
                                    old_field.db_column,
                                    rem_field_name,
                                    app_label,
                                    model_name,
                                    field,
                                    field_name,
                                )
                            )
                            old_field_keys.remove(
                                (rem_app_label, rem_model_name, rem_field_name)
                            )
                            old_field_keys.add((app_label, model_name, field_name))
                            self.renamed_fields[app_label, model_name, field_name] = (
                                rem_field_name
                            )
                            break