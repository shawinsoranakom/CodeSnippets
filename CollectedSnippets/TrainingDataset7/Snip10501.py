def add_constraint(self, app_label, model_name, constraint):
        self._append_option(app_label, model_name, "constraints", constraint)