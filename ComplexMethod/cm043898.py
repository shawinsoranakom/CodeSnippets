def validate_country(cls, v):
        """
        Normalize country inputs to ISO3 codes.

        Accepts:
        - ISO3 codes: "USA", "JPN", "GBR"
        - Country names: "United States", "Japan", "United Kingdom"
        - Snake_case names: "united_states", "japan", "united_kingdom"
        - Wildcards: "*" or "all" to include all countries
        - None: Allowed if dimension_values contains a country dimension (validated in model_validator)
        """
        # pylint: disable=import-outside-toplevel
        from openbb_imf.utils.metadata import ImfMetadata

        # Allow None - will be validated in model_validator with dimension_values check
        if not v:
            return None

        # Split by comma, handling potential spaces and filtering empty strings
        items = [c.strip() for c in v.split(",") if c.strip()]

        if not items:
            return None

        # Check for wildcards - return early without metadata lookup
        if len(items) == 1 and items[0].lower() in ("*", "all"):
            return "*"

        metadata = ImfMetadata()
        country_codes = metadata._codelist_cache.get("CL_COUNTRY", {})

        # Build lookup tables
        code_set = set(country_codes.keys())
        name_to_code: dict[str, str] = {}
        for code, name in country_codes.items():
            # Add lowercase name
            name_to_code[name.lower()] = code
            # Add snake_case version (replace spaces with underscores)
            snake_name = (
                name.lower()
                .replace(" ", "_")
                .replace(",", "")
                .replace(".", "")
                .replace("'", "")
            )
            name_to_code[snake_name] = code

        result: list[str] = []

        for item in items:
            item_upper = item.upper().strip()
            item_lower = item.lower().strip().replace(" ", "_")

            # Handle wildcards in mixed input
            if item_lower in ("*", "all"):
                return "*"  # Wildcard overrides everything

            # Check if it's already an ISO3 code
            if item_upper in code_set:
                result.append(item_upper)
            # Check if it's a name (with spaces or snake_case)
            elif item_lower in name_to_code:
                result.append(name_to_code[item_lower])
            # Try with original casing as lowercase lookup
            elif item.lower() in name_to_code:
                result.append(name_to_code[item.lower()])
            else:
                # Not found - pass through as uppercase (will fail later with clearer error)
                result.append(item_upper)

        return ",".join(result)