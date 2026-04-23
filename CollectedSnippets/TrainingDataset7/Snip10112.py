def _get_generated_field_dependencies_for_removed_field(
        self, app_label, model_name, field_name
    ):
        dependencies = []
        model_state = self.from_state.models[app_label, model_name]
        generated_fields = (f for f in model_state.fields.values() if f.generated)
        for field in generated_fields:
            if any(
                field_name == name
                for name, *_ in models.Model._get_expr_references(field.expression)
            ):
                dependencies.append(
                    OperationDependency(
                        app_label,
                        model_name,
                        field.name,
                        OperationDependency.Type.REMOVE,
                    )
                )
        return dependencies