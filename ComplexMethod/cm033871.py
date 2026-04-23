def record_deprecation(self, name: str, deprecation: dict[str, t.Any] | None, collection_name: str) -> t.Self:
        if self.ignore_deprecated or not deprecation:
            return self

        # The `or ''` instead of using `.get(..., '')` makes sure that even if the user explicitly
        # sets `warning_text` to `~` (None) or `false`, we still get an empty string.
        warning_text = deprecation.get('warning_text', None) or ''
        removal_date = deprecation.get('removal_date', None)
        removal_version = deprecation.get('removal_version', None)
        # If both removal_date and removal_version are specified, use removal_date
        if removal_date is not None:
            removal_version = None
        warning_text = '{0} has been deprecated.{1}{2}'.format(name, ' ' if warning_text else '', warning_text)

        display.deprecated(  # pylint: disable=ansible-deprecated-date-not-permitted,ansible-deprecated-unnecessary-collection-name
            msg=warning_text,
            date=removal_date,
            version=removal_version,
            deprecator=deprecator_from_collection_name(collection_name),
            obj=name,
        )

        self.deprecated = True
        if removal_date:
            self.removal_date = removal_date
        if removal_version:
            self.removal_version = removal_version
        self.deprecation_warnings.append(warning_text)
        return self