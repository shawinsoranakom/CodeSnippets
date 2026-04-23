def _model_supports_natural_key(self, model):
        """Return True if the model defines a natural_key() method."""
        try:
            return callable(model.natural_key)
        except AttributeError:
            return False