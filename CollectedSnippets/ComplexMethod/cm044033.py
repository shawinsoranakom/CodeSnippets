def country_validate(cls, v):
        """Validate countries."""
        if v is None:
            return "g20"
        new_countries: list = []
        if isinstance(v, str):
            countries = v.split(",")
        elif isinstance(v, list):
            countries = v
        if "all" in countries:
            return "all"
        for country in countries:
            if country.lower() not in COUNTRY_CHOICES:
                warn(f"Country {country} not supported, skipping...")
            else:
                new_countries.append(country)
        if not new_countries:
            raise OpenBBError("No valid countries found.")
        return ",".join(new_countries)