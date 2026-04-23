def add_issue(self, issue: Issue) -> None:
        """Add or update an issue in the list. Create or update a repair if necessary."""
        if issue.key in ISSUE_KEYS_FOR_REPAIRS:
            if not issue.suggestions and issue.key in EXTRA_PLACEHOLDERS:
                placeholders: dict[str, str] = EXTRA_PLACEHOLDERS[issue.key].copy()
            else:
                placeholders = {}

            if issue.reference:
                placeholders[PLACEHOLDER_KEY_REFERENCE] = issue.reference

                if issue.key in {
                    ISSUE_KEY_ADDON_DETACHED_ADDON_MISSING,
                    ISSUE_KEY_ADDON_PWNED,
                }:
                    placeholders[PLACEHOLDER_KEY_ADDON_URL] = (
                        f"/hassio/addon/{issue.reference}"
                    )
                    addons_list = get_addons_list(self._hass) or []
                    placeholders[PLACEHOLDER_KEY_ADDON] = issue.reference
                    for addon in addons_list:
                        if addon[ATTR_SLUG] == issue.reference:
                            placeholders[PLACEHOLDER_KEY_ADDON] = addon[ATTR_NAME]
                            break

            elif issue.key == ISSUE_KEY_SYSTEM_FREE_SPACE:
                host_info = get_host_info(self._hass)
                if host_info and "disk_free" in host_info:
                    placeholders[PLACEHOLDER_KEY_FREE_SPACE] = str(
                        host_info["disk_free"]
                    )
                else:
                    placeholders[PLACEHOLDER_KEY_FREE_SPACE] = "<2"

            if issue.key == ISSUE_MOUNT_MOUNT_FAILED:
                self._async_coordinator_refresh()

            async_create_issue(
                self._hass,
                DOMAIN,
                issue.uuid.hex,
                is_fixable=bool(issue.suggestions),
                severity=IssueSeverity.WARNING,
                translation_key=issue.key,
                translation_placeholders=placeholders or None,
            )

        self._issues[issue.uuid] = issue