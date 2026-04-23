def state_forwards(self, app_label, state):
        state.add_model(
            ModelState(
                app_label,
                self.name,
                list(self.fields),
                dict(self.options),
                tuple(self.bases),
                list(self.managers),
            )
        )