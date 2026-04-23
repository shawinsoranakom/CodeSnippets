async def _get_team_members_financial_data(
        client: httpx.AsyncClient,
        team_id: str,
    ) -> dict:
        """
        Get financial data for all members in a team.

        Fetches team info from LiteLLM and extracts spending/budget data for each member.

        Args:
            client: HTTP client for LiteLLM API
            team_id: The team/organization ID

        Returns:
            Dict with structure:
            {
                "team_max_budget": float | None,  # Team's shared budget
                "team_spend": float,              # Team's total spend (for shared budget calc)
                "members": {
                    user_id: {
                        "spend": float,
                        "max_budget": float | None,
                        "uses_shared_budget": bool  # True if using team budget
                    },
                    ...
                }
            }
            Returns empty dict if team not found or LiteLLM is not configured.
        """
        if LITE_LLM_API_KEY is None or LITE_LLM_API_URL is None:
            logger.warning('LiteLLM API configuration not found')
            return {}

        team_info = await LiteLlmManager._get_team(client, team_id)
        if not team_info:
            logger.warning(
                'LiteLlmManager:_get_team_members_financial_data:team_not_found',
                extra={'team_id': team_id},
            )
            return {}

        members: dict[str, dict] = {}
        team_memberships = team_info.get('team_memberships', [])

        # Get team-level budget info (shared across all members in team orgs)
        team_data = team_info.get('team_info', {})
        team_max_budget = team_data.get('max_budget')
        team_spend = team_data.get('spend', 0) or 0

        for membership in team_memberships:
            user_id = membership.get('user_id')
            if not user_id:
                continue

            # Use individual max_budget_in_team if set, otherwise fall back to team budget
            member_max_budget = membership.get('max_budget_in_team')
            uses_shared_budget = member_max_budget is None
            if uses_shared_budget:
                member_max_budget = team_max_budget

            members[user_id] = {
                'spend': membership.get('spend', 0) or 0,
                'max_budget': member_max_budget,
                'uses_shared_budget': uses_shared_budget,
            }

        logger.debug(
            'LiteLlmManager:_get_team_members_financial_data:success',
            extra={'team_id': team_id, 'member_count': len(members)},
        )
        return {
            'team_max_budget': team_max_budget,
            'team_spend': team_spend,
            'members': members,
        }