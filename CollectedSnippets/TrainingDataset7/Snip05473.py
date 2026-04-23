def _is_default_auto_field_overridden(self):
        return self.__class__.default_auto_field is not AppConfig.default_auto_field