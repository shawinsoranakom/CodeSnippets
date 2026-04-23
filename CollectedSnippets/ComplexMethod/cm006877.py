def normalize_value(cls, v):
        """Convert simple string or list of strings to list of dicts format.

        Allows passing:
        - 'gpt-4o' -> [{'name': 'gpt-4o', ...}]
        - ['gpt-4o', 'claude-3'] -> [{'name': 'gpt-4o', ...}, {'name': 'claude-3', ...}]
        - [{'name': 'gpt-4o'}] -> [{'name': 'gpt-4o'}] (unchanged)
        - 'connect_other_models' -> 'connect_other_models' (special value, keep as string)
        """
        # Handle empty or None values — normalize all to None so that
        # ``self.<model_field>`` is None when nothing is selected.
        if v is None or v in ("", []):
            return None

        # Special case: keep "connect_other_models" as a string to enable connection mode
        if v == "connect_other_models":
            return v

        # If it's not a list or string, return as-is (could be a BaseLanguageModel)
        if not isinstance(v, list | str):
            return v

        # If it's a list and already in dict format, return as-is
        if isinstance(v, list) and all(isinstance(item, dict) for item in v):
            return v

        # If it's a string or list of strings, convert to dict format
        if isinstance(v, str) or (isinstance(v, list) and all(isinstance(item, str) for item in v)):
            # Avoid circular import by importing the module directly (not through package __init__)
            try:
                from lfx.base.models.unified_models import normalize_model_names_to_dicts

                return normalize_model_names_to_dicts(v)
            except Exception:  # noqa: BLE001
                # Fallback if import or normalization fails
                # This can happen during module initialization or in test environments
                if isinstance(v, str):
                    return [{"name": v}]
                return [{"name": item} for item in v]

        # Return as-is for all other cases
        return v