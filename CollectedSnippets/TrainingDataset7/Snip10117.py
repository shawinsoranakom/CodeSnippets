def _generate_altered_foo_together(self, operation):
        for (
            old_value,
            new_value,
            app_label,
            model_name,
            dependencies,
        ) in self._get_altered_foo_together_operations(operation.option_name):
            removal_value = new_value.intersection(old_value)
            if new_value != removal_value:
                self.add_operation(
                    app_label,
                    operation(name=model_name, **{operation.option_name: new_value}),
                    dependencies=dependencies,
                )