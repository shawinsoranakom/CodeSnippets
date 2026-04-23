async def create_entries(
        org_id: str,
        keycloak_user_id: str,
        oss_settings: Settings,
        create_user: bool,
    ) -> Settings | None:
        logger.info(
            'SettingsStore:update_settings_with_litellm_default:start',
            extra={'org_id': org_id, 'user_id': keycloak_user_id},
        )
        if LITE_LLM_API_KEY is None or LITE_LLM_API_URL is None:
            logger.warning('LiteLLM API configuration not found')
            return None
        local_deploy = os.environ.get('LOCAL_DEPLOYMENT', None)
        key = LITE_LLM_API_KEY
        if not local_deploy:
            # Get user info to add to litellm
            token_manager = TokenManager()
            keycloak_user_info = (
                await token_manager.get_user_info_from_user_id(keycloak_user_id) or {}
            )

            async with httpx.AsyncClient(
                headers={
                    'x-goog-api-key': LITE_LLM_API_KEY,
                }
            ) as client:
                # Check if team already exists and get its budget
                # New users joining existing orgs should inherit the team's budget
                # When billing is disabled, DEFAULT_INITIAL_BUDGET is None
                team_budget: float | None = DEFAULT_INITIAL_BUDGET
                try:
                    existing_team = await LiteLlmManager._get_team(client, org_id)
                    if existing_team:
                        team_info = existing_team.get('team_info', {})
                        # Preserve None from existing team (no budget enforcement)
                        existing_budget = team_info.get('max_budget')
                        team_budget = existing_budget
                        logger.info(
                            'LiteLlmManager:create_entries:existing_team_budget',
                            extra={
                                'org_id': org_id,
                                'user_id': keycloak_user_id,
                                'team_budget': team_budget,
                            },
                        )
                except httpx.HTTPStatusError as e:
                    # Team doesn't exist yet (404) - this is expected for first user
                    if e.response.status_code != 404:
                        raise
                    logger.info(
                        'LiteLlmManager:create_entries:no_existing_team',
                        extra={'org_id': org_id, 'user_id': keycloak_user_id},
                    )

                await LiteLlmManager._create_team(
                    client, keycloak_user_id, org_id, team_budget
                )

                if create_user:
                    user_created = await LiteLlmManager._create_user(
                        client, keycloak_user_info.get('email'), keycloak_user_id
                    )
                    if not user_created:
                        logger.error(
                            'create_entries_failed_user_creation',
                            extra={
                                'org_id': org_id,
                                'user_id': keycloak_user_id,
                            },
                        )
                        return None

                # Verify user exists before proceeding with key generation
                user_exists = await LiteLlmManager._user_exists(
                    client, keycloak_user_id
                )
                if not user_exists:
                    logger.error(
                        'create_entries_user_not_found_before_key_generation',
                        extra={
                            'org_id': org_id,
                            'user_id': keycloak_user_id,
                            'create_user_flag': create_user,
                        },
                    )
                    return None

                await LiteLlmManager._add_user_to_team(
                    client, keycloak_user_id, org_id, team_budget
                )

                # We delete the key if it already exists. In environments where multiple
                # installations are using the same keycloak and litellm instance, this
                # will mean other installations will have their key invalidated.
                key_alias = get_openhands_cloud_key_alias(keycloak_user_id, org_id)
                try:
                    await LiteLlmManager._delete_key_by_alias(client, key_alias)
                except httpx.HTTPStatusError as ex:
                    if ex.status_code == 404:
                        logger.debug(f'Key "{key_alias}" did not exist - continuing')
                    else:
                        raise

                key = await LiteLlmManager._generate_key(
                    client,
                    keycloak_user_id,
                    org_id,
                    key_alias,
                    None,
                )

        oss_settings.update(
            {
                'agent_settings_diff': {
                    'agent': 'CodeActAgent',
                    'llm': {
                        'model': get_default_litellm_model(),
                        'api_key': key,
                        'base_url': LITE_LLM_API_URL,
                    },
                }
            }
        )
        return oss_settings