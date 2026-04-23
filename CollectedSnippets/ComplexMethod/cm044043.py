def _validate_country(cls, v):
        """Validate country."""
        if not v:
            return None

        if v and isinstance(v, list) and not v[0]:
            return None

        countries = v

        if isinstance(countries, str):
            countries = [countries] if "," not in countries else countries.split(",")

        if not isinstance(countries, list):
            raise ValueError(
                f"Country must be a string or list of strings. Got {type(v)}"
            )

        if isinstance(countries, list) and len(countries) == 1 and "," in countries[0]:
            countries = countries[0].split(",")

        invalid_countries = [
            country
            for country in countries
            if country
            and country not in COUNTRY_CHOICES.values()
            and country not in COUNTRY_CHOICES
        ]

        if invalid_countries:
            raise ValueError(
                f"Invalid country code(s) '{', '.join(invalid_countries)}'. Valid country codes are: "
                + ", ".join(
                    sorted(list(COUNTRY_CHOICES)),
                )
            )

        return v