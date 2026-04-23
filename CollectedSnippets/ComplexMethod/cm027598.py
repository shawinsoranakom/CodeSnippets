def _validate_placeholders(
        self,
        language: str,
        updated_resources: dict[str, str],
        cached_resources: dict[str, str] | None = None,
    ) -> dict[str, str]:
        """Validate if updated resources have same placeholders as cached resources."""
        if cached_resources is None:
            return updated_resources

        mismatches: set[str] = set()

        for key, value in updated_resources.items():
            if key not in cached_resources:
                continue
            try:
                tuples = list(string.Formatter().parse(value))
            except ValueError:
                _LOGGER.error(
                    ("Error while parsing localized (%s) string %s"), language, key
                )
                continue
            updated_placeholders = {tup[1] for tup in tuples if tup[1] is not None}

            tuples = list(string.Formatter().parse(cached_resources[key]))
            cached_placeholders = {tup[1] for tup in tuples if tup[1] is not None}
            if updated_placeholders != cached_placeholders:
                _LOGGER.error(
                    (
                        "Validation of translation placeholders for localized (%s) string "
                        "%s failed: (%s != %s)"
                    ),
                    language,
                    key,
                    updated_placeholders,
                    cached_placeholders,
                )
                mismatches.add(key)

        for mismatch in mismatches:
            del updated_resources[mismatch]

        return updated_resources