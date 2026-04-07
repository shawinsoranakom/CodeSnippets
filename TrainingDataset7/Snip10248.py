def state_forwards(self, app_label, state):
        state.rename_field(
            app_label, self.model_name_lower, self.old_name, self.new_name
        )