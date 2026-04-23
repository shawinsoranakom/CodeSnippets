async def downgrade_entries(
        org_id: str,
        keycloak_user_id: str,
        user_settings: UserSettings,
    ) -> UserSettings | None:
        """Downgrade a migrated user's LiteLLM entries back to the pre-migration state.

        This reverses the migrate_entries operation:
        1. Get the user max budget from their org team in litellm
        2. Set the max budget in the user in litellm (restore from team)
        3. Add the user back to the default team in litellm
        4. Update keys to remove org team association
        5. Remove the user from their org team in litellm
        6. Delete the user org team in litellm

        Note: The database changes (already_migrated flag, org/org_member deletion)
        should be handled separately by the caller.

        Args:
            org_id: The organization ID (which is also the team_id in litellm)
            keycloak_user_id: The user's Keycloak ID
            user_settings: The user's settings object

        Returns:
            The user_settings if downgrade was successful, None otherwise
        """
        logger.info(
            'LiteLlmManager:downgrade_entries:start',
            extra={'org_id': org_id, 'user_id': keycloak_user_id},
        )
        if LITE_LLM_API_KEY is None or LITE_LLM_API_URL is None:
            logger.warning('LiteLLM API configuration not found')
            return None

        local_deploy = os.environ.get('LOCAL_DEPLOYMENT', None)
        if not local_deploy:
            async with httpx.AsyncClient(
                headers={
                    'x-goog-api-key': LITE_LLM_API_KEY,
                }
            ) as client:
                # Step 1: Get the team info to retrieve the budget
                logger.debug(
                    'LiteLlmManager:downgrade_entries:get_team',
                    extra={'org_id': org_id, 'user_id': keycloak_user_id},
                )
                team_info = await LiteLlmManager._get_team(client, org_id)
                if not team_info:
                    logger.error(
                        'LiteLlmManager:downgrade_entries:team_not_found',
                        extra={'org_id': org_id, 'user_id': keycloak_user_id},
                    )
                    return None

                # Get team budget (max_budget) and spend to calculate current credits
                team_data = team_info.get('team_info', {})
                max_budget = team_data.get('max_budget', 0.0)
                spend = team_data.get('spend', 0.0)

                # Get user membership info for budget in team
                user_membership = await LiteLlmManager._get_user_team_info(
                    client, keycloak_user_id, org_id
                )
                if user_membership:
                    # Use user's budget in team if available
                    user_max_budget_in_team = user_membership.get('max_budget_in_team')
                    user_spend_in_team = user_membership.get('spend', 0.0)
                    if user_max_budget_in_team is not None:
                        max_budget = user_max_budget_in_team
                        spend = user_spend_in_team

                # Calculate total budget to restore (credits + spend = max_budget)
                # We restore the full max_budget that was on the team/user-in-team
                restored_budget = max_budget if max_budget else 0.0

                logger.debug(
                    'LiteLlmManager:downgrade_entries:budget_info',
                    extra={
                        'org_id': org_id,
                        'user_id': keycloak_user_id,
                        'max_budget': max_budget,
                        'spend': spend,
                        'restored_budget': restored_budget,
                    },
                )

                # Step 2: Update user to set their max_budget back from unlimited
                logger.debug(
                    'LiteLlmManager:downgrade_entries:update_user',
                    extra={'org_id': org_id, 'user_id': keycloak_user_id},
                )
                await LiteLlmManager._update_user(
                    client, keycloak_user_id, max_budget=restored_budget, spend=spend
                )

                # Step 3: Add user back to the default team
                if LITE_LLM_TEAM_ID:
                    logger.debug(
                        'LiteLlmManager:downgrade_entries:add_to_default_team',
                        extra={
                            'org_id': org_id,
                            'user_id': keycloak_user_id,
                            'default_team_id': LITE_LLM_TEAM_ID,
                        },
                    )
                    await LiteLlmManager._add_user_to_team(
                        client, keycloak_user_id, LITE_LLM_TEAM_ID, restored_budget
                    )

                # Step 4: Update all user keys to remove org team association (set team_id to default)
                logger.debug(
                    'LiteLlmManager:downgrade_entries:update_user_keys',
                    extra={'org_id': org_id, 'user_id': keycloak_user_id},
                )
                await LiteLlmManager._update_user_keys(
                    client,
                    keycloak_user_id,
                    team_id=LITE_LLM_TEAM_ID,
                )

                # Step 5: Remove user from their org team
                logger.debug(
                    'LiteLlmManager:downgrade_entries:remove_from_org_team',
                    extra={'org_id': org_id, 'user_id': keycloak_user_id},
                )
                await LiteLlmManager._remove_user_from_team(
                    client, keycloak_user_id, org_id
                )

                # Step 6: Delete the org team
                logger.debug(
                    'LiteLlmManager:downgrade_entries:delete_team',
                    extra={'org_id': org_id, 'user_id': keycloak_user_id},
                )
                await LiteLlmManager._delete_team(client, org_id)

        logger.info(
            'LiteLlmManager:downgrade_entries:complete',
            extra={'org_id': org_id, 'user_id': keycloak_user_id},
        )
        return user_settings