def validate_countries(cls, v):
        """Validate each country and convert to a two-letter ISO code."""
        # pylint: disable=import-outside-toplevel
        from openbb_econdb.utils import helpers

        if v:
            country = v if isinstance(v, list) else v.split(",")
            for c in country.copy():
                c = "all" if c == "world" else c  # noqa: PLW2901
                if c == "all":
                    continue
                if (
                    len(c) == 2
                    and c.upper() not in list(helpers.COUNTRY_MAP.values())
                    and c.lower() != "g7"
                ):
                    country.remove(c)
                elif len(c) == 3 and c.lower() != "g20":
                    _c = helpers.THREE_LETTER_ISO_MAP.get(c.upper(), "")
                    if _c:
                        country[country.index(c)] = _c
                    else:
                        warn(f"Error: {c} is not a valid country code.")
                        country.remove(c)
                elif len(c) > 3 and c.lower() in helpers.COUNTRY_MAP:
                    country[country.index(c)] = helpers.COUNTRY_MAP[c.lower()].upper()
                elif len(c) > 2 and c.lower() in helpers.COUNTRY_GROUPS:
                    country[country.index(c)] = ",".join(
                        helpers.COUNTRY_GROUPS[c.lower()]
                    )
            if len(country) == 0:
                raise OpenBBError("No valid countries were supplied.")
            return ",".join(country)
        return None