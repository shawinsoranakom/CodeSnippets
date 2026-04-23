def validate_country(cls, v):
        """Validate the country."""
        # pylint: disable=import-outside-toplevel
        from openbb_econdb.utils.helpers import (
            COUNTRY_GROUPS,
            COUNTRY_MAP,
            INDICATOR_COUNTRIES,
            THREE_LETTER_ISO_MAP,
        )

        country = v if isinstance(v, list) else v.split(",")

        if "all" in country:
            return ",".join(INDICATOR_COUNTRIES.get("RGDP"))

        for c in country.copy():
            if (
                len(c) == 2
                and c.upper() not in list(COUNTRY_MAP.values())
                and c.lower() != "g7"
            ) or (
                len(c) > 3 and c.lower() not in list(COUNTRY_MAP) + list(COUNTRY_GROUPS)
            ):
                country.remove(c)
            elif len(c) == 3 and c.lower() != "g20":
                _c = THREE_LETTER_ISO_MAP.get(c.upper(), "")
                if _c:  # pylint: disable=R0801
                    country[country.index(c)] = _c
                else:
                    warn(f"Error: {c} is not a valid country code.")
                    country.remove(c)
            elif len(c) > 3 and c.lower() in COUNTRY_MAP:
                country[country.index(c)] = COUNTRY_MAP[c.lower()].upper()
            elif len(c) > 2 and c.lower() in COUNTRY_GROUPS:
                country[country.index(c)] = ",".join(COUNTRY_GROUPS[c.lower()])
        if len(country) == 0:
            raise OpenBBError("No valid countries were supplied.")
        return ",".join(country)