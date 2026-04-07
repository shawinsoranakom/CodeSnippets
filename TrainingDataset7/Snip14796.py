def _get_explicit_or_implicit_cause(self, exc_value):
        explicit = getattr(exc_value, "__cause__", None)
        suppress_context = getattr(exc_value, "__suppress_context__", None)
        implicit = getattr(exc_value, "__context__", None)
        return explicit or (None if suppress_context else implicit)