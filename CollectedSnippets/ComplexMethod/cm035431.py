async def _handle_action(self, event: Action) -> None:
        if event.timeout is None:
            # We don't block the command if this is a default timeout action
            event.set_hard_timeout(self.config.sandbox.timeout, blocking=False)
        assert event.timeout is not None
        try:
            await self._export_latest_git_provider_tokens(event)
            if isinstance(event, MCPAction):
                observation: Observation = await self.call_tool_mcp(event)
            else:
                observation = await call_sync_from_async(self.run_action, event)
        except PermissionError as e:
            # Handle PermissionError specially - convert to ErrorObservation
            # so the agent can receive feedback and continue execution
            observation = ErrorObservation(content=str(e))
        except (httpx.NetworkError, AgentRuntimeDisconnectedError) as e:
            runtime_status = RuntimeStatus.ERROR_RUNTIME_DISCONNECTED
            error_message = f'{type(e).__name__}: {str(e)}'
            self.log('error', f'Unexpected error while running action: {error_message}')
            self.log('error', f'Problematic action: {str(event)}')
            self.set_runtime_status(runtime_status, error_message, level='error')
            return
        except Exception as e:
            runtime_status = RuntimeStatus.ERROR
            error_message = f'{type(e).__name__}: {str(e)}'
            self.log('error', f'Unexpected error while running action: {error_message}')
            self.log('error', f'Problematic action: {str(event)}')
            self.set_runtime_status(runtime_status, error_message, level='error')
            return

        observation._cause = event.id  # type: ignore[attr-defined]
        observation.tool_call_metadata = event.tool_call_metadata

        # this might be unnecessary, since source should be set by the event stream when we're here
        source = event.source if event.source else EventSource.AGENT
        if isinstance(observation, NullObservation):
            # don't add null observations to the event stream
            return
        self.event_stream.add_event(observation, source)