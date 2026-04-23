def disable_action(self, name):
        """
        Disable a globally-registered action. Raise KeyError for invalid names.
        """
        del self._actions[name]