def __repr__(self):
        return "%s(%s=%s)" % (
            pretty_name(self),
            self._default_unit,
            getattr(self, self._default_unit),
        )