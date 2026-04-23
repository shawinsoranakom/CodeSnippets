async def _get_user_team_info(
        client: httpx.AsyncClient,
        keycloak_user_id: str,
        team_id: str,
    ) -> dict | None:
        if LITE_LLM_API_KEY is None or LITE_LLM_API_URL is None:
            logger.warning('LiteLLM API configuration not found')
            return None
        team_response = await LiteLlmManager._get_team(client, team_id)
        if not team_response:
            return None

        # Filter team_memberships based on team_id and keycloak_user_id
        user_membership = next(
            (
                membership
                for membership in team_response.get('team_memberships', [])
                if membership.get('user_id') == keycloak_user_id
                and membership.get('team_id') == team_id
            ),
            None,
        )

        if not user_membership:
            return None

        # For team orgs (user_id != team_id), include team-level budget info
        # The team's max_budget and spend are shared across all members
        if keycloak_user_id != team_id:
            team_info = team_response.get('team_info', {})
            user_membership['max_budget_in_team'] = team_info.get('max_budget')
            user_membership['spend'] = team_info.get('spend', 0)

        return user_membership