def state_forwards(self, app_label, state):
        state.remove_constraint(app_label, self.model_name_lower, self.name)