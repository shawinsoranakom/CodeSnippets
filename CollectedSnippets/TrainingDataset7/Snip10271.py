def state_forwards(self, app_label, state):
        state.remove_model(app_label, self.name_lower)