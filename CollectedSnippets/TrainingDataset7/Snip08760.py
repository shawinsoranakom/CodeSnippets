def handle(self, **options):
        from django.conf import Settings, global_settings, settings

        # Because settings are imported lazily, we need to explicitly load
        # them.
        if not settings.configured:
            settings._setup()

        user_settings = module_to_dict(settings._wrapped)
        default = options["default"]
        default_settings = module_to_dict(
            Settings(default) if default else global_settings
        )
        output_func = {
            "hash": self.output_hash,
            "unified": self.output_unified,
        }[options["output"]]
        return "\n".join(output_func(user_settings, default_settings, **options))