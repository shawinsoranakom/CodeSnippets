def base_location(self):
        return self._value_or_setting(self._location, settings.MEDIA_ROOT)