def generate_altered_constraints(self):
        for (
            app_label,
            model_name,
        ), alt_constraints in self.altered_constraints.items():
            dependencies = self._get_dependencies_for_model(app_label, model_name)
            for constraint in alt_constraints["altered_constraints"]:
                self.add_operation(
                    app_label,
                    operations.AlterConstraint(
                        model_name=model_name,
                        name=constraint.name,
                        constraint=constraint,
                    ),
                    dependencies=dependencies,
                )