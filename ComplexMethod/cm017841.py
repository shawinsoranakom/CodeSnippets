def cleanse_setting(self, key, value):
        """
        Cleanse an individual setting key/value of sensitive content. If the
        value is a dictionary, recursively cleanse the keys in that dictionary.
        """
        if key == settings.SESSION_COOKIE_NAME:
            is_sensitive = True
        else:
            try:
                is_sensitive = self.hidden_settings.search(key)
            except TypeError:
                is_sensitive = False

        if is_sensitive:
            cleansed = self.cleansed_substitute
        elif isinstance(value, dict):
            cleansed = {k: self.cleanse_setting(k, v) for k, v in value.items()}
        elif isinstance(value, list):
            cleansed = [self.cleanse_setting("", v) for v in value]
        elif isinstance(value, tuple):
            cleansed = tuple([self.cleanse_setting("", v) for v in value])
        else:
            cleansed = value

        if callable(cleansed):
            cleansed = CallableSettingWrapper(cleansed)

        return cleansed