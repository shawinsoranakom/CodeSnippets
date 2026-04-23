def _resolve_fk_natural_key(self, obj, field):
        """
        Return the natural key for a ForeignKey's related object, or None if
        not supported.
        """
        if not self._model_supports_natural_key(field.remote_field.model):
            return None

        related = getattr(obj, field.name, None)
        try:
            return related.natural_key()
        except AttributeError:
            return None