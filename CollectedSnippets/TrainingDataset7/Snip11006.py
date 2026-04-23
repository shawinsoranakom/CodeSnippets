def __repr__(self):
        """Display the module, class, and name of the field."""
        path = "%s.%s" % (self.__class__.__module__, self.__class__.__qualname__)
        name = getattr(self, "name", None)
        if name is not None:
            return "<%s: %s>" % (path, name)
        return "<%s>" % path