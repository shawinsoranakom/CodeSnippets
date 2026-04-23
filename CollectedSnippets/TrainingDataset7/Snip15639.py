def handle_app_config(self, app_config, **options):
        print(
            "EXECUTE:AppCommand name=%s, options=%s"
            % (app_config.name, sorted(options.items()))
        )