def get_model(self, app_label, model_name=None, require_ready=True):
        """
        Return the model matching the given app_label and model_name.

        As a shortcut, app_label may be in the form <app_label>.<model_name>.

        model_name is case-insensitive.

        Raise LookupError if no application exists with this label, or no
        model exists with this name in the application. Raise ValueError if
        called with a single argument that doesn't contain exactly one dot.
        """
        if require_ready:
            self.check_models_ready()
        else:
            self.check_apps_ready()

        if model_name is None:
            app_label, model_name = app_label.split(".")

        app_config = self.get_app_config(app_label)

        if not require_ready and app_config.models is None:
            app_config.import_models()

        return app_config.get_model(model_name, require_ready=require_ready)