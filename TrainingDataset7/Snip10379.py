def state_forwards(self, app_label, state):
        state.alter_constraint(
            app_label, self.model_name_lower, self.name, self.constraint
        )