def handle_app_config(self, app_config, **options):
        """
        Perform the command's actions for app_config, an AppConfig instance
        corresponding to an application label given on the command line.
        """
        raise NotImplementedError(
            "Subclasses of AppCommand must provide a handle_app_config() method."
        )