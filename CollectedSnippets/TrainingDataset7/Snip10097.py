def _generate_added_field(self, app_label, model_name, field_name):
        field = self.to_state.models[app_label, model_name].get_field(field_name)
        # Adding a field always depends at least on its removal.
        dependencies = [
            OperationDependency(
                app_label, model_name, field_name, OperationDependency.Type.REMOVE
            )
        ]
        # Fields that are foreignkeys/m2ms depend on stuff.
        if field.remote_field and field.remote_field.model:
            dependencies.extend(
                self._get_dependencies_for_foreign_key(
                    app_label,
                    model_name,
                    field,
                    self.to_state,
                )
            )
        if field.generated:
            dependencies.extend(self._get_dependencies_for_generated_field(field))
        # You can't just add NOT NULL fields with no default or fields
        # which don't allow empty strings as default.
        time_fields = (models.DateField, models.DateTimeField, models.TimeField)
        auto_fields = (models.AutoField, models.SmallAutoField, models.BigAutoField)
        preserve_default = (
            field.null
            or field.has_default()
            or field.has_db_default()
            or field.many_to_many
            or (field.blank and field.empty_strings_allowed)
            or (isinstance(field, time_fields) and field.auto_now)
            or (isinstance(field, auto_fields))
        )
        if not preserve_default:
            field = field.clone()
            if isinstance(field, time_fields) and field.auto_now_add:
                field.default = self.questioner.ask_auto_now_add_addition(
                    field_name, model_name
                )
            else:
                field.default = self.questioner.ask_not_null_addition(
                    field_name, model_name
                )
        if field.unique and field.has_default() and callable(field.default):
            self.questioner.ask_unique_callable_default_addition(field_name, model_name)
        self.add_operation(
            app_label,
            operations.AddField(
                model_name=model_name,
                name=field_name,
                field=field,
                preserve_default=preserve_default,
            ),
            dependencies=dependencies,
        )