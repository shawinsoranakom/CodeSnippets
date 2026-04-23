async def start_job(self, github_view: GithubViewType) -> None:
        """Kick off a job with openhands agent using V1 app conversation system.

        1. Get user credential
        2. Initialize new conversation with repo
        3. Save interaction data
        """
        try:
            msg_info: str = ''

            try:
                user_info = github_view.user_info
                logger.info(
                    f'[GitHub] Starting job for user {user_info.username} (id={user_info.user_id})'
                )

                # Create conversation
                user_token = await self.token_manager.get_idp_token_from_idp_user_id(
                    str(user_info.user_id), ProviderType.GITHUB
                )

                if not user_token:
                    logger.warning(
                        f'[GitHub] No token found for user {user_info.username} (id={user_info.user_id})'
                    )
                    raise MissingSettingsError('Missing settings')

                logger.info(
                    f'[GitHub] Creating new conversation for user {user_info.username}'
                )

                secret_store = Secrets(
                    provider_tokens=MappingProxyType(
                        {
                            ProviderType.GITHUB: ProviderToken(
                                token=SecretStr(user_token),
                                user_id=str(user_info.user_id),
                            )
                        }
                    )
                )

                # We first initialize a conversation and generate the solvability report BEFORE starting the conversation runtime
                # This helps us accumulate llm spend without requiring a running runtime. This setups us up for
                #   1. If there is a problem starting the runtime we still have accumulated total conversation cost
                #   2. In the future, based on the report confidence we can conditionally start the conversation
                #   3. Once the conversation is started, its base cost will include the report's spend as well which allows us to control max budget per resolver task
                convo_metadata = await github_view.initialize_new_conversation()
                solvability_summary = None
                if not ENABLE_SOLVABILITY_ANALYSIS:
                    logger.info(
                        '[Github]: Solvability report feature is disabled, skipping'
                    )
                else:
                    try:
                        solvability_summary = await summarize_issue_solvability(
                            github_view, user_token
                        )
                    except Exception as e:
                        logger.warning(
                            f'[Github]: Error summarizing issue solvability: {str(e)}'
                        )

                saas_user_auth = await get_saas_user_auth(
                    github_view.user_info.keycloak_user_id, self.token_manager
                )

                await github_view.create_new_conversation(
                    self.jinja_env,
                    secret_store.provider_tokens,
                    convo_metadata,
                    saas_user_auth,
                )

                conversation_id = github_view.conversation_id

                logger.info(
                    f'[GitHub] Created conversation {conversation_id} for user {user_info.username}'
                )

                # V1 callback processors are registered by the view during conversation creation

                # Send message with conversation link
                conversation_link = CONVERSATION_URL.format(conversation_id)
                base_msg = f"I'm on it! {user_info.username} can [track my progress at all-hands.dev]({conversation_link})"
                # Combine messages: include solvability report with "I'm on it!" if successful
                if solvability_summary:
                    msg_info = f'{base_msg}\n\n{solvability_summary}'
                else:
                    msg_info = base_msg

            except MissingSettingsError as e:
                logger.warning(
                    f'[GitHub] Missing settings error for user {user_info.username}: {str(e)}'
                )

                msg_info = f'@{user_info.username} please re-login into [OpenHands Cloud]({HOST_URL}) before starting a job.'

            except LLMAuthenticationError as e:
                logger.warning(
                    f'[GitHub] LLM authentication error for user {user_info.username}: {str(e)}'
                )

                msg_info = f'@{user_info.username} please set a valid LLM API key in [OpenHands Cloud]({HOST_URL}) before starting a job.'

            except (AuthenticationError, ExpiredError, SessionExpiredError) as e:
                logger.warning(
                    f'[GitHub] Session expired for user {user_info.username}: {str(e)}'
                )

                msg_info = get_session_expired_message(user_info.username)

            await self.send_message(msg_info, github_view)

        except Exception:
            logger.exception('[Github]: Error starting job')
            await self.send_message(
                'Uh oh! There was an unexpected error starting the job :(', github_view
            )

        try:
            await self.data_collector.save_data(github_view)
        except Exception:
            logger.warning('[Github]: Error saving interaction data', exc_info=True)