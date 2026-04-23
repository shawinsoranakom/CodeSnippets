async def get_conversation_hooks(
    conversation_id: UUID,
    app_conversation_service: AppConversationService = (
        app_conversation_service_dependency
    ),
    sandbox_service: SandboxService = sandbox_service_dependency,
    sandbox_spec_service: SandboxSpecService = sandbox_spec_service_dependency,
    httpx_client: httpx.AsyncClient = httpx_client_dependency,
) -> JSONResponse:
    """Get hooks currently configured in the workspace for this conversation.

    This endpoint loads hooks from the conversation's project directory in the
    workspace (i.e. `{project_dir}/.openhands/hooks.json`) at request time.

    Note:
        This is intentionally a "live" view of the workspace configuration.
        If `.openhands/hooks.json` changes over time, this endpoint reflects the
        latest file content and may not match the hooks that were used when the
        conversation originally started.

    Returns:
        JSONResponse: A JSON response containing the list of hook event types.
        Returns an empty list if the sandbox is not running.
    """
    try:
        # Get agent server context (conversation, sandbox, sandbox_spec, agent_server_url)
        ctx = await _get_agent_server_context(
            conversation_id,
            app_conversation_service,
            sandbox_service,
            sandbox_spec_service,
        )
        if isinstance(ctx, JSONResponse):
            return ctx
        if ctx is None:
            return JSONResponse(status_code=status.HTTP_200_OK, content={'hooks': []})

        from openhands.app_server.app_conversation.hook_loader import (
            fetch_hooks_from_agent_server,
            get_project_dir_for_hooks,
        )

        project_dir = get_project_dir_for_hooks(
            ctx.sandbox_spec.working_dir,
            ctx.conversation.selected_repository,
        )

        # Load hooks from agent-server (using the error-raising variant so
        # HTTP/connection failures are surfaced to the user, not hidden).
        logger.debug(
            f'Loading hooks for conversation {conversation_id}, '
            f'agent_server_url={ctx.agent_server_url}, '
            f'project_dir={project_dir}'
        )

        try:
            hook_config = await fetch_hooks_from_agent_server(
                agent_server_url=ctx.agent_server_url,
                session_api_key=ctx.session_api_key,
                project_dir=project_dir,
                httpx_client=httpx_client,
            )
        except httpx.HTTPStatusError as e:
            logger.warning(
                f'Agent-server returned {e.response.status_code} when loading hooks '
                f'for conversation {conversation_id}: {e.response.text}'
            )
            return JSONResponse(
                status_code=status.HTTP_502_BAD_GATEWAY,
                content={
                    'error': f'Agent-server returned status {e.response.status_code} when loading hooks'
                },
            )
        except httpx.RequestError as e:
            logger.warning(
                f'Failed to reach agent-server when loading hooks '
                f'for conversation {conversation_id}: {e}'
            )
            return JSONResponse(
                status_code=status.HTTP_502_BAD_GATEWAY,
                content={'error': 'Failed to reach agent-server when loading hooks'},
            )

        # Transform hook_config to response format
        hooks_response: list[HookEventResponse] = []

        if hook_config:
            # Define the event types to check
            event_types = [
                'pre_tool_use',
                'post_tool_use',
                'user_prompt_submit',
                'session_start',
                'session_end',
                'stop',
            ]

            for field_name in event_types:
                matchers = getattr(hook_config, field_name, [])
                if matchers:
                    matcher_responses = []
                    for matcher in matchers:
                        hook_defs = [
                            HookDefinitionResponse(
                                type=hook.type.value
                                if hasattr(hook.type, 'value')
                                else str(hook.type),
                                command=hook.command,
                                timeout=hook.timeout,
                                async_=hook.async_,
                            )
                            for hook in matcher.hooks
                        ]
                        matcher_responses.append(
                            HookMatcherResponse(
                                matcher=matcher.matcher,
                                hooks=hook_defs,
                            )
                        )
                    hooks_response.append(
                        HookEventResponse(
                            event_type=field_name,
                            matchers=matcher_responses,
                        )
                    )

        logger.debug(
            f'Loaded {len(hooks_response)} hook event types for conversation {conversation_id}'
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=GetHooksResponse(hooks=hooks_response).model_dump(by_alias=True),
        )

    except Exception as e:
        logger.error(f'Error getting hooks for conversation {conversation_id}: {e}')
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={'error': f'Error getting hooks: {str(e)}'},
        )