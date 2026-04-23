async def poll_agent_servers(api_url: str, api_key: str, sleep_interval: int):
    """When the app server does not have a public facing url, we poll the agent
    servers for the most recent data.

    This is because webhook callbacks cannot be invoked."""
    from openhands.app_server.config import (
        get_app_conversation_info_service,
        get_event_callback_service,
        get_event_service,
        get_httpx_client,
    )

    while True:
        try:
            # Refresh the conversations associated with those sandboxes.
            state = InjectorState()

            try:
                # Get the list of running sandboxes using the runtime api /list endpoint.
                # (This will not return runtimes that have been stopped for a while)
                async with get_httpx_client(state) as httpx_client:
                    response = await httpx_client.get(
                        f'{api_url}/list', headers={'X-API-Key': api_key}
                    )
                    response.raise_for_status()
                    runtimes = response.json()['runtimes']
                    runtimes_by_sandbox_id = {
                        runtime['session_id']: runtime
                        for runtime in runtimes
                        # The runtime API currently reports a running status when
                        # pods are still starting. Resync can tolerate this.
                        if runtime['status'] == 'running'
                    }

                # We allow access to all items here
                setattr(state, USER_CONTEXT_ATTR, ADMIN)
                async with (
                    get_app_conversation_info_service(
                        state
                    ) as app_conversation_info_service,
                    get_event_service(state) as event_service,
                    get_event_callback_service(state) as event_callback_service,
                    get_httpx_client(state) as httpx_client,
                ):
                    matches = 0
                    async for app_conversation_info in page_iterator(
                        app_conversation_info_service.search_app_conversation_info
                    ):
                        runtime = runtimes_by_sandbox_id.get(
                            app_conversation_info.sandbox_id
                        )
                        if runtime:
                            matches += 1
                            await refresh_conversation(
                                app_conversation_info_service=app_conversation_info_service,
                                event_service=event_service,
                                event_callback_service=event_callback_service,
                                app_conversation_info=app_conversation_info,
                                runtime=runtime,
                                httpx_client=httpx_client,
                            )
                    _logger.debug(
                        f'Matched {len(runtimes_by_sandbox_id)} Runtimes with {matches} Conversations.'
                    )

            except Exception as exc:
                _logger.exception(
                    f'Error when polling agent servers: {exc}', stack_info=True
                )

            # Sleep between retries
            await asyncio.sleep(sleep_interval)

        except asyncio.CancelledError:
            return