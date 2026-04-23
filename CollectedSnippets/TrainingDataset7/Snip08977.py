def _resolve_natural_key(self, obj):
        """Return a natural key tuple for the given object when available."""
        try:
            return obj.natural_key()
        except AttributeError:
            return None