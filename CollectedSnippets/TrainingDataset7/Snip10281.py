def state_forwards(self, app_label, state):
        state.rename_model(app_label, self.old_name, self.new_name)