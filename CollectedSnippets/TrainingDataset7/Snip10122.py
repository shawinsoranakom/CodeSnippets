def generate_altered_order_with_respect_to(self):
        for app_label, model_name in sorted(self.kept_model_keys):
            old_model_name = self.renamed_models.get(
                (app_label, model_name), model_name
            )
            old_model_state = self.from_state.models[app_label, old_model_name]
            new_model_state = self.to_state.models[app_label, model_name]
            if old_model_state.options.get(
                "order_with_respect_to"
            ) != new_model_state.options.get("order_with_respect_to"):
                # Make sure it comes second if we're adding
                # (removal dependency is part of RemoveField)
                dependencies = []
                if new_model_state.options.get("order_with_respect_to"):
                    dependencies.append(
                        OperationDependency(
                            app_label,
                            model_name,
                            new_model_state.options["order_with_respect_to"],
                            OperationDependency.Type.CREATE,
                        )
                    )
                # Actually generate the operation
                self.add_operation(
                    app_label,
                    operations.AlterOrderWithRespectTo(
                        name=model_name,
                        order_with_respect_to=new_model_state.options.get(
                            "order_with_respect_to"
                        ),
                    ),
                    dependencies=dependencies,
                )