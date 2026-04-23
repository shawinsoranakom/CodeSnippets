def _validate_country_fields(cls, v):
        """Validate country and counterpart fields.

        Accepts both ISO3 codes (e.g., 'USA') and snake_case country names
        (e.g., 'united_states'). Converts names to ISO3 codes.
        """
        if not v:
            raise ValueError("Required parameter for IMF provider not supplied.")

        if isinstance(v, str) and v.lower() in ["all", "*"]:
            return "*"

        # Split by comma if string
        values = (
            v.split(",")
            if isinstance(v, str) and "," in v
            else [v] if isinstance(v, str) else v
        )

        result: list[str] = []
        for item in values:
            item_stripped = item.strip()
            if item_stripped.lower() in ["all", "*"]:
                if len(values) > 1:
                    raise ValueError(
                        "'all' cannot be used with other country codes in a list."
                    )
                return "*"
            # Resolve the country input (handles both codes and names)
            resolved = resolve_country_input(item_stripped)
            result.append(resolved)

        return ",".join(result)