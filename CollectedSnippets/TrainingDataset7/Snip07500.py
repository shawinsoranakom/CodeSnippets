def __str__(self):
        return "%s %s" % (getattr(self, self._default_unit), self._default_unit)