def generate_removed_constraints(self):
        for (
            app_label,
            model_name,
        ), alt_constraints in self.altered_constraints.items():
            for constraint in alt_constraints["removed_constraints"]:
                self.add_operation(
                    app_label,
                    operations.RemoveConstraint(
                        model_name=model_name,
                        name=constraint.name,
                    ),
                )