def state_forwards(self, app_label, state):
        state.alter_model_managers(app_label, self.name_lower, self.managers)