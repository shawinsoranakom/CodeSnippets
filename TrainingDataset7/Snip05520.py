def is_overridden(self, setting):
        deleted = setting in self._deleted
        set_locally = setting in self.__dict__
        set_on_default = getattr(
            self.default_settings, "is_overridden", lambda s: False
        )(setting)
        return deleted or set_locally or set_on_default