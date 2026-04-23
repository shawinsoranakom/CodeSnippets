def validate_country(cls, v):
        """Validate country.

        Accepts Country type, ISO codes, country names, or snake_case names.
        Converts all inputs to Nasdaq's expected snake_case format.
        """
        if isinstance(v, Country):
            # Convert Country to snake_case name
            v = v.name.lower().replace(" ", "_").replace("-", "_")
        v = v.split(",")
        new_items = []
        for item in v:
            if item == "all":
                continue
            # Try to convert via Country type if not already valid
            normalized_item = item
            if item not in list(get_args(COUNTRY_CHOICES)):
                try:
                    country = Country(item)
                    normalized_item = (
                        country.name.lower().replace(" ", "_").replace("-", "_")
                    )
                except ValueError:
                    pass  # Keep original, will warn below
            if normalized_item in list(get_args(COUNTRY_CHOICES)):
                new_items.append(normalized_item)
            else:
                warn(f"Invalid country: {item}")
        return ",".join(new_items) if new_items else "all"