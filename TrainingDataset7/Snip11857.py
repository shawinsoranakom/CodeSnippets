def app_config(self):
        # Don't go through get_app_config to avoid triggering imports.
        return self.apps.app_configs.get(self.app_label)