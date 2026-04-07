def run_setup(self, app_config_name):
        custom_settings = override_settings(
            INSTALLED_APPS=[f"apps.query_performing_app.apps.{app_config_name}"]
        )
        custom_settings.enable()
        old_stored_app_configs = apps.stored_app_configs
        apps.stored_app_configs = []
        try:
            with patch.multiple(apps, ready=False, loading=False, app_configs={}):
                with self.assertWarnsMessage(RuntimeWarning, self.expected_msg):
                    django.setup()

                app_config = apps.get_app_config("query_performing_app")
                return app_config.query_results
        finally:
            setattr(apps, "stored_app_configs", old_stored_app_configs)
            custom_settings.disable()