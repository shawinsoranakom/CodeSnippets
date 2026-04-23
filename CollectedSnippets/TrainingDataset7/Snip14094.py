def __repr__(self):
        if isinstance(self.urlconf_name, list) and self.urlconf_name:
            # Don't bother to output the whole list, it can be huge
            urlconf_repr = "<%s list>" % self.urlconf_name[0].__class__.__name__
        else:
            urlconf_repr = repr(self.urlconf_name)
        return "<%s %s (%s:%s) %s>" % (
            self.__class__.__name__,
            urlconf_repr,
            self.app_name,
            self.namespace,
            self.pattern.describe(),
        )