def ask_rename_model(self, old_model_state, new_model_state):
        """Was this model really renamed?"""
        msg = "Was the model %s.%s renamed to %s? [y/N]"
        return self._boolean_input(
            msg
            % (old_model_state.app_label, old_model_state.name, new_model_state.name),
            False,
        )