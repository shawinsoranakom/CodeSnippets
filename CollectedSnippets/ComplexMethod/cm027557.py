def score(
        self, dialect: Dialect, country: str | None = None
    ) -> tuple[float, float]:
        """Return score for match with another dialect where higher is better.

        Score < 0 indicates a failure to match.
        """
        if not is_language_match(self.language, dialect.language):
            # Not a match
            return (-1, 0)

        is_exact_language = self.language == dialect.language
        is_exact_language_and_code = is_exact_language and (self.code == dialect.code)

        if (self.region is None) and (dialect.region is None):
            # Weak match with no region constraint
            # Prefer exact language match
            if is_exact_language_and_code:
                return (3, 0)

            if is_exact_language:
                return (2, 0)

            return (1, 0)

        if (self.region is not None) and (dialect.region is not None):
            if self.region == dialect.region:
                # Same language + region match
                # Prefer exact language match
                if is_exact_language_and_code:
                    return (math.inf, 2)

                if is_exact_language:
                    return (math.inf, 1)

                return (math.inf, 0)

            # Regions are both set, but don't match
            return (0, 0)

        # Generate ordered list of preferred regions
        pref_regions = list(
            preferred_regions(
                self.language,
                country=country,
                code=self.code,
            )
        )

        try:
            # Determine score based on position in the preferred regions list.
            if self.region is not None:
                region_idx = pref_regions.index(self.region)
            elif dialect.region is not None:
                region_idx = pref_regions.index(dialect.region)

            # More preferred regions are at the front.
            # Add 2 to boost above a weak match where no regions are set.
            return (2 + (len(pref_regions) - region_idx), 0)
        except ValueError:
            # Region was not in preferred list
            pass

        # Not a preferred region
        return (0, 0)