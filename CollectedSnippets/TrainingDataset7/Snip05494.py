def unset_available_apps(self):
        """Cancel a previous call to set_available_apps()."""
        self.app_configs = self.stored_app_configs.pop()
        self.clear_cache()