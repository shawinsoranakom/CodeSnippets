def _get_model_from_node(model_identifier):
        """Look up a model from an "app_label.model_name" string."""
        try:
            return apps.get_model(model_identifier)
        except (LookupError, TypeError):
            raise base.DeserializationError(
                f"Invalid model identifier: {model_identifier}"
            )