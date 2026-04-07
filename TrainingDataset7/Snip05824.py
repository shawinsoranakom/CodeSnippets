def actions(self):
        """
        Get all the enabled actions as an iterable of (name, func).
        """
        return self._actions.items()