def reload_models(self, models, delay=True):
        if "apps" in self.__dict__:  # hasattr would cache the property
            related_models = set()
            for app_label, model_name in models:
                related_models.update(
                    self._find_reload_model(app_label, model_name, delay)
                )
            self._reload(related_models)