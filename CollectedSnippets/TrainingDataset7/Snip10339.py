def state_forwards(self, app_label, state):
        state.add_index(app_label, self.model_name_lower, self.index)