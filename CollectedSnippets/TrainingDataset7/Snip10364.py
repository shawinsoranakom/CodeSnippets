def state_forwards(self, app_label, state):
        state.add_constraint(app_label, self.model_name_lower, self.constraint)