def normalize_model_options(cls, v):
        """Convert simple list of model names to list of dicts format.

        Allows passing ['gpt-4o', 'gpt-4o-mini'] which gets converted to:
        [{'name': 'gpt-4o', ...}, {'name': 'gpt-4o-mini', ...}]
        """
        if v is None or not isinstance(v, list):
            return v

        # If already in dict format, return as-is
        if all(isinstance(item, dict) for item in v):
            return v

        # If it's a list of strings, convert to dict format
        if all(isinstance(item, str) for item in v):
            # Avoid circular import by importing the module directly (not through package __init__)
            try:
                from lfx.base.models.unified_models import normalize_model_names_to_dicts

                return normalize_model_names_to_dicts(v)
            except Exception:  # noqa: BLE001
                # Fallback if import or normalization fails
                # This can happen during module initialization or in test environments
                return [{"name": item} for item in v]

        # Mixed list or unexpected format, return as-is
        return v