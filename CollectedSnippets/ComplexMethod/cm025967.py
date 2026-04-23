async def async_create_fix_flow(
    hass: HomeAssistant,
    issue_id: str,
    data: dict[str, str | int | float | None] | None,
) -> RepairsFlow:
    """Create flow."""
    supervisor_issues = get_issues_info(hass)
    issue = supervisor_issues and supervisor_issues.get_issue(issue_id)
    if issue and issue.key == ISSUE_KEY_SYSTEM_DOCKER_CONFIG:
        return DockerConfigIssueRepairFlow(hass, issue_id)
    if issue and issue.key == ISSUE_KEY_ADDON_DEPRECATED:
        return DeprecatedAddonIssueRepairFlow(hass, issue_id)
    if issue and issue.key in {
        ISSUE_KEY_ADDON_DETACHED_ADDON_REMOVED,
        ISSUE_KEY_ADDON_BOOT_FAIL,
        ISSUE_KEY_ADDON_PWNED,
        ISSUE_KEY_ADDON_DEPRECATED_ARCH,
    }:
        return AddonIssueRepairFlow(hass, issue_id)

    return SupervisorIssueRepairFlow(hass, issue_id)