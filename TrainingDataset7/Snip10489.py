def add_model(self, model_state):
        model_key = model_state.app_label, model_state.name_lower
        self.models[model_key] = model_state
        if self._relations is not None:
            self.resolve_model_relations(model_key)
        if "apps" in self.__dict__:  # hasattr would cache the property
            self.reload_model(*model_key)