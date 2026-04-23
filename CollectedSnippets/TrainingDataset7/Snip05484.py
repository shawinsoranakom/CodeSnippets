def get_app_configs(self):
        """Import applications and return an iterable of app configs."""
        self.check_apps_ready()
        return self.app_configs.values()