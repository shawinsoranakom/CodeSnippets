def get_model(self, model_name, require_ready=True):
        """
        Return the model with the given case-insensitive model_name.

        Raise LookupError if no model exists with this name.
        """
        if require_ready:
            self.apps.check_models_ready()
        else:
            self.apps.check_apps_ready()
        try:
            return self.models[model_name.lower()]
        except KeyError:
            raise LookupError(
                "App '%s' doesn't have a '%s' model." % (self.label, model_name)
            )