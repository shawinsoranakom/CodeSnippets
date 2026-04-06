def is_enabled(self):
        """Returns `True` when rule enabled.

        :rtype: bool

        """
        return (
            self.name in settings.rules
            or self.enabled_by_default
            and ALL_ENABLED in settings.rules
        )