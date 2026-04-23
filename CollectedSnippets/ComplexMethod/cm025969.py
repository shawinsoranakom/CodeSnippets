def description_placeholders(self) -> dict[str, str] | None:
        """Get description placeholders for steps."""
        placeholders: dict[str, str] = super().description_placeholders or {}
        if self.issue and self.issue.reference:
            addons_list = get_addons_list(self.hass) or []
            placeholders[PLACEHOLDER_KEY_ADDON] = self.issue.reference
            for addon in addons_list:
                if addon[ATTR_SLUG] == self.issue.reference:
                    placeholders[PLACEHOLDER_KEY_ADDON] = addon[ATTR_NAME]
                    break

        return placeholders or None