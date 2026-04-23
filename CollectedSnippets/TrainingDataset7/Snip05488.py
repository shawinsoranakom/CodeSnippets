def register_model(self, app_label, model):
        # Since this method is called when models are imported, it cannot
        # perform imports because of the risk of import loops. It mustn't
        # call get_app_config().
        model_name = model._meta.model_name
        app_models = self.all_models[app_label]
        if model_name in app_models:
            if (
                model.__name__ == app_models[model_name].__name__
                and model.__module__ == app_models[model_name].__module__
            ):
                warnings.warn(
                    "Model '%s.%s' was already registered. Reloading models is not "
                    "advised as it can lead to inconsistencies, most notably with "
                    "related models." % (app_label, model_name),
                    RuntimeWarning,
                    stacklevel=2,
                )
            else:
                raise RuntimeError(
                    "Conflicting '%s' models in application '%s': %s and %s."
                    % (model_name, app_label, app_models[model_name], model)
                )
        app_models[model_name] = model
        self.do_pending_operations(model)
        self.clear_cache()