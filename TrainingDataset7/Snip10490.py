def remove_model(self, app_label, model_name):
        model_key = app_label, model_name
        del self.models[model_key]
        if self._relations is not None:
            self._relations.pop(model_key, None)
            # Call list() since _relations can change size during iteration.
            for related_model_key, model_relations in list(self._relations.items()):
                model_relations.pop(model_key, None)
                if not model_relations:
                    del self._relations[related_model_key]
        if "apps" in self.__dict__:  # hasattr would cache the property
            self.apps.unregister_model(*model_key)
            # Need to do this explicitly since unregister_model() doesn't clear
            # the cache automatically (#24513)
            self.apps.clear_cache()