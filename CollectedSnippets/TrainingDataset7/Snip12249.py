def check_alias(self, alias):
        # RemovedInDjango70Warning: When the deprecation ends, remove.
        if "%" in alias:
            warnings.warn(
                "Using percent signs in a column alias is deprecated.",
                category=RemovedInDjango70Warning,
                skip_file_prefixes=django_file_prefixes(),
            )
        if FORBIDDEN_ALIAS_PATTERN.search(alias):
            raise ValueError(
                "Column aliases cannot contain whitespace characters, hashes, "
                # RemovedInDjango70Warning: When the deprecation ends, replace
                # with:
                # "control characters, quotation marks, semicolons, percent "
                # "signs, or SQL comments."
                "control characters, quotation marks, semicolons, or SQL comments."
            )