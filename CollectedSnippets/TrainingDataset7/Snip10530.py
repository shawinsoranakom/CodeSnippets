def register_model(self, app_label, model):
        self.all_models[app_label][model._meta.model_name] = model
        if app_label not in self.app_configs:
            self.app_configs[app_label] = AppConfigStub(app_label)
            self.app_configs[app_label].apps = self
        self.app_configs[app_label].models[model._meta.model_name] = model
        self.do_pending_operations(model)
        self.clear_cache()