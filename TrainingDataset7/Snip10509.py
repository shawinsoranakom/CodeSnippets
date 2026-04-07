def reload_model(self, app_label, model_name, delay=False):
        if "apps" in self.__dict__:  # hasattr would cache the property
            related_models = self._find_reload_model(app_label, model_name, delay)
            self._reload(related_models)