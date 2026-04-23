def clone(self):
        """Return a clone of this registry."""
        clone = StateApps([], {})
        clone.all_models = copy.deepcopy(self.all_models)

        for app_label in self.app_configs:
            app_config = AppConfigStub(app_label)
            app_config.apps = clone
            app_config.import_models()
            clone.app_configs[app_label] = app_config

        # No need to actually clone them, they'll never change
        clone.real_models = self.real_models
        return clone