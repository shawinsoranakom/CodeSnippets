def description_placeholders(self) -> dict[str, str] | None:
        """Get description placeholders for steps."""
        placeholders = {PLACEHOLDER_KEY_COMPONENTS: ""}
        supervisor_issues = get_issues_info(self.hass)
        if supervisor_issues and self.issue:
            addons_list = get_addons_list(self.hass) or []
            components: list[str] = []
            for issue in supervisor_issues.issues:
                if issue.key == self.issue.key or issue.type != self.issue.type:
                    continue

                if issue.context == ContextType.CORE:
                    components.insert(0, "Home Assistant")
                elif issue.context == ContextType.ADDON:
                    components.append(
                        next(
                            (
                                addon[ATTR_NAME]
                                for addon in addons_list
                                if addon[ATTR_SLUG] == issue.reference
                            ),
                            issue.reference or "",
                        )
                    )

            placeholders[PLACEHOLDER_KEY_COMPONENTS] = "\n- ".join(components)

        return placeholders