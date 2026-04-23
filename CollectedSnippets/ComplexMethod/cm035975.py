async def migrate_entries(
        org_id: str,
        keycloak_user_id: str,
        user_settings: UserSettings,
    ) -> UserSettings | None:
        logger.info(
            'LiteLlmManager:migrate_lite_llm_entries:start',
            extra={'org_id': org_id, 'user_id': keycloak_user_id},
        )
        if LITE_LLM_API_KEY is None or LITE_LLM_API_URL is None:
            logger.warning('LiteLLM API configuration not found')
            return None
        local_deploy = os.environ.get('LOCAL_DEPLOYMENT', None)
        if not local_deploy:
            # Get user info to add to litellm
            async with httpx.AsyncClient(
                headers={
                    'x-goog-api-key': LITE_LLM_API_KEY,
                }
            ) as client:
                user_json = await LiteLlmManager._get_user(client, keycloak_user_id)
                if not user_json:
                    return None
                user_info = user_json['user_info']

                # Log original user values before any modifications for debugging
                original_max_budget = user_info.get('max_budget')
                original_spend = user_info.get('spend')
                logger.info(
                    'LiteLlmManager:migrate_lite_llm_entries:original_user_values',
                    extra={
                        'org_id': org_id,
                        'user_id': keycloak_user_id,
                        'original_max_budget': original_max_budget,
                        'original_spend': original_spend,
                    },
                )

                max_budget = (
                    original_max_budget if original_max_budget is not None else 0.0
                )
                spend = original_spend if original_spend is not None else 0.0
                # In upgrade to V4, we no longer use billing margin, but instead apply this directly
                # in litellm. The default billing marign was 2 before this (hence the magic numbers below)
                if (
                    user_settings
                    and user_settings.user_version < 4
                    and user_settings.billing_margin
                    and user_settings.billing_margin != 1.0
                ):
                    billing_margin = user_settings.billing_margin
                    logger.info(
                        'user_settings_v4_budget_upgrade',
                        extra={
                            'max_budget': max_budget,
                            'billing_margin': billing_margin,
                            'spend': spend,
                        },
                    )
                    max_budget *= billing_margin
                    spend *= billing_margin

                # Check if max_budget is None (not 0.0) or set to unlimited to determine if already migrated
                # A user with max_budget=0.0 is different from max_budget=None
                if (
                    original_max_budget is None
                    or original_max_budget == UNLIMITED_BUDGET_SETTING
                ):
                    # if max_budget is None or UNLIMITED, then we've already migrated the User
                    logger.info(
                        'LiteLlmManager:migrate_lite_llm_entries:already_migrated',
                        extra={
                            'org_id': org_id,
                            'user_id': keycloak_user_id,
                            'original_max_budget': original_max_budget,
                        },
                    )
                    return None
                credits = max(max_budget - spend, 0.0)

                # Log calculated migration values before performing updates
                logger.info(
                    'LiteLlmManager:migrate_lite_llm_entries:calculated_values',
                    extra={
                        'org_id': org_id,
                        'user_id': keycloak_user_id,
                        'adjusted_max_budget': max_budget,
                        'adjusted_spend': spend,
                        'calculated_credits': credits,
                        'new_user_max_budget': UNLIMITED_BUDGET_SETTING,
                    },
                )

                logger.debug(
                    'LiteLlmManager:migrate_lite_llm_entries:create_team',
                    extra={'org_id': org_id, 'user_id': keycloak_user_id},
                )
                await LiteLlmManager._create_team(
                    client, keycloak_user_id, org_id, credits
                )

                logger.debug(
                    'LiteLlmManager:migrate_lite_llm_entries:update_user',
                    extra={'org_id': org_id, 'user_id': keycloak_user_id},
                )
                await LiteLlmManager._update_user(
                    client, keycloak_user_id, max_budget=UNLIMITED_BUDGET_SETTING
                )

                logger.debug(
                    'LiteLlmManager:migrate_lite_llm_entries:add_user_to_team',
                    extra={'org_id': org_id, 'user_id': keycloak_user_id},
                )
                await LiteLlmManager._add_user_to_team(
                    client, keycloak_user_id, org_id, credits
                )

                logger.debug(
                    'LiteLlmManager:migrate_lite_llm_entries:update_user_keys',
                    extra={'org_id': org_id, 'user_id': keycloak_user_id},
                )
                await LiteLlmManager._update_user_keys(
                    client,
                    keycloak_user_id,
                    team_id=org_id,
                )

                # Check if the database key exists in LiteLLM
                # If not, generate a new key to prevent verification failures later
                db_key = None
                llm_base_url = None
                # agent_settings is a JSON column (dict) on UserSettings
                llm_cfg = (
                    (user_settings.agent_settings or {}).get('llm', {})
                    if user_settings
                    else {}
                )
                llm_base_url = llm_cfg.get('base_url')
                if llm_base_url == LITE_LLM_API_URL:
                    db_key = llm_cfg.get('api_key')
                    if hasattr(db_key, 'get_secret_value'):
                        db_key = db_key.get_secret_value()

                if db_key:
                    # Verify the database key exists in LiteLLM
                    key_valid = await LiteLlmManager.verify_key(
                        db_key, keycloak_user_id
                    )
                    if not key_valid:
                        logger.warning(
                            'LiteLlmManager:migrate_lite_llm_entries:db_key_not_in_litellm',
                            extra={
                                'org_id': org_id,
                                'user_id': keycloak_user_id,
                                'key_prefix': db_key[:10] + '...'
                                if len(db_key) > 10
                                else db_key,
                            },
                        )
                        # Generate a new key for the user
                        new_key = await LiteLlmManager._generate_key(
                            client,
                            keycloak_user_id,
                            org_id,
                            get_openhands_cloud_key_alias(keycloak_user_id, org_id),
                            None,
                        )
                        logger.info(
                            'LiteLlmManager:migrate_lite_llm_entries:generated_new_key',
                            extra={'org_id': org_id, 'user_id': keycloak_user_id},
                        )
                        # Update user_settings with the new key so it gets stored in org_member
                        # agent_settings is a non-nullable JSON column (dict) on UserSettings
                        user_settings.agent_settings.setdefault('llm', {})[
                            'api_key'
                        ] = new_key
                        user_settings.llm_api_key_for_byor_secret = SecretStr(new_key)

        logger.info(
            'LiteLlmManager:migrate_lite_llm_entries:complete',
            extra={'org_id': org_id, 'user_id': keycloak_user_id},
        )
        return user_settings