def _get_validated_env_list() -> list[str]:
        value = os.getenv(env_name)
        if value is None:
            return default

        # Split comma-separated values and strip whitespace
        values = [v.strip() for v in value.split(",") if v.strip()]

        if not values:
            return default

        # Resolve choices if it's a callable (for lazy loading)
        actual_choices = choices() if callable(choices) else choices

        # Validate each value
        for val in values:
            if not case_sensitive:
                check_value = val.lower()
                check_choices = [choice.lower() for choice in actual_choices]
            else:
                check_value = val
                check_choices = actual_choices

            if check_value not in check_choices:
                raise ValueError(
                    f"Invalid value '{val}' in {env_name}. "
                    f"Valid options: {actual_choices}."
                )

        return values