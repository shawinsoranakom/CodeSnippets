def alter_constraint(self, app_label, model_name, constraint_name, constraint):
        self._alter_option(
            app_label, model_name, "constraints", constraint_name, constraint
        )