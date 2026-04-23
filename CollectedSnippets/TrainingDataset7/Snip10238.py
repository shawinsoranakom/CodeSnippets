def state_forwards(self, app_label, state):
        state.alter_field(
            app_label,
            self.model_name_lower,
            self.name,
            self.field,
            self.preserve_default,
        )