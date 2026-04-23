async def inject(
        self, state: InjectorState, request: Request | None = None
    ) -> AsyncGenerator[AppConversationService, None]:
        from openhands.app_server.config import (
            get_app_conversation_info_service,
            get_app_conversation_start_task_service,
            get_event_service,
            get_global_config,
            get_httpx_client,
            get_jwt_service,
            get_pending_message_service,
            get_sandbox_service,
            get_sandbox_spec_service,
            get_user_context,
        )

        async with (
            get_user_context(state, request) as user_context,
            get_sandbox_service(state, request) as sandbox_service,
            get_sandbox_spec_service(state, request) as sandbox_spec_service,
            get_app_conversation_info_service(
                state, request
            ) as app_conversation_info_service,
            get_app_conversation_start_task_service(
                state, request
            ) as app_conversation_start_task_service,
            get_event_callback_service(state, request) as event_callback_service,
            get_event_service(state, request) as event_service,
            get_jwt_service(state, request) as jwt_service,
            get_httpx_client(state, request) as httpx_client,
            get_pending_message_service(state, request) as pending_message_service,
        ):
            access_token_hard_timeout = None
            if self.access_token_hard_timeout:
                access_token_hard_timeout = timedelta(
                    seconds=float(self.access_token_hard_timeout)
                )
            config = get_global_config()

            # If no web url has been set and we are using docker, we can use host.docker.internal
            web_url = config.web_url
            if web_url is None:
                if isinstance(sandbox_service, DockerSandboxService):
                    web_url = f'http://host.docker.internal:{sandbox_service.host_port}'

            # Get app_mode for SaaS mode
            app_mode = None
            try:
                from openhands.server.shared import server_config

                app_mode = (
                    server_config.app_mode.value if server_config.app_mode else None
                )
            except (ImportError, AttributeError):
                # If server_config is not available (e.g., in tests), continue without it
                pass

            # We supply the global tavily key only if the app mode is not SAAS, where
            # currently the search endpoints are patched into the app server instead
            # so the tavily key does not need to be shared
            if self.tavily_api_key and app_mode != AppMode.SAAS:
                tavily_api_key = self.tavily_api_key.get_secret_value()
            else:
                tavily_api_key = None

            yield LiveStatusAppConversationService(
                init_git_in_empty_workspace=self.init_git_in_empty_workspace,
                user_context=user_context,
                sandbox_service=sandbox_service,
                sandbox_spec_service=sandbox_spec_service,
                app_conversation_info_service=app_conversation_info_service,
                app_conversation_start_task_service=app_conversation_start_task_service,
                event_callback_service=event_callback_service,
                event_service=event_service,
                jwt_service=jwt_service,
                pending_message_service=pending_message_service,
                sandbox_startup_timeout=self.sandbox_startup_timeout,
                sandbox_startup_poll_frequency=self.sandbox_startup_poll_frequency,
                max_num_conversations_per_sandbox=self.max_num_conversations_per_sandbox,
                httpx_client=httpx_client,
                web_url=web_url,
                openhands_provider_base_url=config.openhands_provider_base_url,
                access_token_hard_timeout=access_token_hard_timeout,
                app_mode=app_mode,
                tavily_api_key=tavily_api_key,
            )