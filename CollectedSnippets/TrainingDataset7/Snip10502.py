def remove_constraint(self, app_label, model_name, constraint_name):
        self._remove_option(app_label, model_name, "constraints", constraint_name)