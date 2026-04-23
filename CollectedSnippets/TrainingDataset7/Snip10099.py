def _generate_removed_field(self, app_label, model_name, field_name):
        self.add_operation(
            app_label,
            operations.RemoveField(
                model_name=model_name,
                name=field_name,
            ),
            # Include dependencies such as order_with_respect_to, constraints,
            # and any generated fields that may depend on this field. These
            # are safely ignored if not present.
            dependencies=[
                OperationDependency(
                    app_label,
                    model_name,
                    field_name,
                    OperationDependency.Type.REMOVE_ORDER_WRT,
                ),
                OperationDependency(
                    app_label,
                    model_name,
                    field_name,
                    OperationDependency.Type.ALTER_FOO_TOGETHER,
                ),
                OperationDependency(
                    app_label,
                    model_name,
                    field_name,
                    OperationDependency.Type.REMOVE_INDEX_OR_CONSTRAINT,
                ),
                *self._get_generated_field_dependencies_for_removed_field(
                    app_label, model_name, field_name
                ),
            ],
        )