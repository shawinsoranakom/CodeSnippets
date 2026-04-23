def __init__(self, settings_module):
        # update this dict from global settings (but only for ALL_CAPS
        # settings)
        for setting in dir(global_settings):
            if setting.isupper():
                setattr(self, setting, getattr(global_settings, setting))

        # store the settings module in case someone later cares
        self.SETTINGS_MODULE = settings_module

        mod = importlib.import_module(self.SETTINGS_MODULE)

        tuple_settings = (
            "ALLOWED_HOSTS",
            "INSTALLED_APPS",
            "TEMPLATE_DIRS",
            "LOCALE_PATHS",
            "SECRET_KEY_FALLBACKS",
        )
        self._explicit_settings = set()
        for setting in dir(mod):
            if setting.isupper():
                setting_value = getattr(mod, setting)

                if setting in tuple_settings and not isinstance(
                    setting_value, (list, tuple)
                ):
                    raise ImproperlyConfigured(
                        "The %s setting must be a list or a tuple." % setting
                    )
                setattr(self, setting, setting_value)
                self._explicit_settings.add(setting)

        if hasattr(time, "tzset") and self.TIME_ZONE:
            # When we can, attempt to validate the timezone. If we can't find
            # this file, no check happens and it's harmless.
            zoneinfo_root = Path("/usr/share/zoneinfo")
            zone_info_file = zoneinfo_root.joinpath(*self.TIME_ZONE.split("/"))
            if zoneinfo_root.exists() and not zone_info_file.exists():
                raise ValueError("Incorrect timezone setting: %s" % self.TIME_ZONE)
            # Move the time zone info into os.environ. See ticket #2315 for why
            # we don't do this unconditionally (breaks Windows).
            os.environ["TZ"] = self.TIME_ZONE
            time.tzset()