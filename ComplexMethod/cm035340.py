async def _on_event(self, event: Event):
        """Handle an event from the event stream asynchronously."""
        try:
            if isinstance(event, RecallAction):
                # if this is a workspace context recall (on first user message)
                # create and add a RecallObservation
                # with info about repo, runtime, instructions, etc. including microagent knowledge if any
                if (
                    event.source == EventSource.USER
                    and event.recall_type == RecallType.WORKSPACE_CONTEXT
                ):
                    logger.debug('Workspace context recall')
                    workspace_obs: RecallObservation | NullObservation | None = None

                    workspace_obs = self._on_workspace_context_recall(event)
                    if workspace_obs is None:
                        workspace_obs = NullObservation(content='')

                    # important: this will release the execution flow from waiting for the retrieval to complete
                    workspace_obs._cause = event.id  # type: ignore[union-attr]

                    self.event_stream.add_event(workspace_obs, EventSource.ENVIRONMENT)
                    return

                # Handle knowledge recall (triggered microagents)
                # Allow triggering from both user and agent messages
                elif (
                    event.source == EventSource.USER
                    or event.source == EventSource.AGENT
                ) and event.recall_type == RecallType.KNOWLEDGE:
                    logger.debug(
                        f'Microagent knowledge recall from {event.source} message'
                    )
                    microagent_obs: RecallObservation | NullObservation | None = None
                    microagent_obs = self._on_microagent_recall(event)
                    if microagent_obs is None:
                        microagent_obs = NullObservation(content='')

                    # important: this will release the execution flow from waiting for the retrieval to complete
                    microagent_obs._cause = event.id  # type: ignore[union-attr]

                    self.event_stream.add_event(microagent_obs, EventSource.ENVIRONMENT)
                    return
        except Exception as e:
            error_str = f'Error: {str(e.__class__.__name__)}'
            logger.error(error_str)
            self.set_runtime_status(RuntimeStatus.ERROR_MEMORY, error_str)
            return