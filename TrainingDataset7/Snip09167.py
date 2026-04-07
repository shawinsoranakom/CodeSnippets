def check_settings(self):
        if self.settings_dict["TIME_ZONE"] is not None and not settings.USE_TZ:
            raise ImproperlyConfigured(
                "Connection '%s' cannot set TIME_ZONE because USE_TZ is False."
                % self.alias
            )