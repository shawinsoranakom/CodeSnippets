def describe(self):
        """
        Output a brief summary of what the action does.
        """
        return "%s: %s" % (self.__class__.__name__, self._constructor_args)