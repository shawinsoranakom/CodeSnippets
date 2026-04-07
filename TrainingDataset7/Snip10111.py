def _get_dependencies_for_generated_field(self, field):
        dependencies = []
        referenced_base_fields = [
            name
            for name, *lookups in models.Model._get_expr_references(field.expression)
        ]
        newly_added_fields = sorted(self.new_field_keys - self.old_field_keys)
        for app_label, model_name, added_field_name in newly_added_fields:
            added_field = self.to_state.models[app_label, model_name].get_field(
                added_field_name
            )
            if (
                added_field.remote_field and added_field.remote_field.model
            ) or added_field.name in referenced_base_fields:
                dependencies.append(
                    OperationDependency(
                        app_label,
                        model_name,
                        added_field.name,
                        OperationDependency.Type.CREATE,
                    )
                )
        return dependencies