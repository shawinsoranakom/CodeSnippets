def mock_resolution_info(
    supervisor_client: AsyncMock,
    unsupported: list[UnsupportedReason] | None = None,
    unhealthy: list[UnhealthyReason] | None = None,
    issues: list[Issue] | None = None,
    suggestions_by_issue: dict[UUID, list[Suggestion]] | None = None,
    suggestion_result: SupervisorError | None = None,
) -> None:
    """Mock resolution/info endpoint with unsupported/unhealthy reasons and/or issues."""
    supervisor_client.resolution.info.return_value = ResolutionInfo(
        unsupported=unsupported or [],
        unhealthy=unhealthy or [],
        issues=issues or [],
        suggestions=[
            suggestion
            for issue_list in suggestions_by_issue.values()
            for suggestion in issue_list
        ]
        if suggestions_by_issue
        else [],
        checks=[
            Check(enabled=True, slug=CheckType.DOCKER_CONFIG),
            Check(enabled=True, slug=CheckType.FREE_SPACE),
        ],
    )

    if suggestions_by_issue:

        async def mock_suggestions_for_issue(uuid: UUID) -> list[Suggestion]:
            """Mock of suggestions for issue api."""
            return suggestions_by_issue.get(uuid, [])

        supervisor_client.resolution.suggestions_for_issue.side_effect = (
            mock_suggestions_for_issue
        )
        supervisor_client.resolution.apply_suggestion.side_effect = suggestion_result