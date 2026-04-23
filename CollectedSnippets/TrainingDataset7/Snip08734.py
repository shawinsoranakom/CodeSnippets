def handle(self, *app_labels, **options):
        from django.apps import apps

        try:
            app_configs = [apps.get_app_config(app_label) for app_label in app_labels]
        except (LookupError, ImportError) as e:
            raise CommandError(
                "%s. Are you sure your INSTALLED_APPS setting is correct?" % e
            )
        output = []
        for app_config in app_configs:
            app_output = self.handle_app_config(app_config, **options)
            if app_output:
                output.append(app_output)
        return "\n".join(output)