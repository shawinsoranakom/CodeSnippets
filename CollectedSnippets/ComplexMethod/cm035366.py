def _reset(self) -> None:
        """Resets the agent controller."""
        # Runnable actions need an Observation
        # make sure there is an Observation with the tool call metadata to be recognized by the agent
        # otherwise the pending action is found in history, but it's incomplete without an obs with tool result
        if self._pending_action and hasattr(self._pending_action, 'tool_call_metadata'):
            # find out if there already is an observation with the same tool call metadata
            found_observation = False
            for event in self.state.history:
                if (
                    isinstance(event, Observation)
                    and event.tool_call_metadata
                    == self._pending_action.tool_call_metadata
                ):
                    found_observation = True
                    break

            # make a new ErrorObservation with the tool call metadata
            if not found_observation:
                # Use different messages and IDs based on whether the agent was stopped by user or due to error
                if self.state.agent_state == AgentState.STOPPED:
                    error_content = ERROR_ACTION_NOT_EXECUTED_STOPPED
                    error_id = ERROR_ACTION_NOT_EXECUTED_STOPPED_ID
                else:  # AgentState.ERROR
                    error_content = ERROR_ACTION_NOT_EXECUTED_ERROR
                    error_id = ERROR_ACTION_NOT_EXECUTED_ERROR_ID

                obs = ErrorObservation(
                    content=error_content,
                    error_id=error_id,
                )
                obs.tool_call_metadata = self._pending_action.tool_call_metadata
                obs._cause = self._pending_action.id  # type: ignore[attr-defined]
                self.event_stream.add_event(obs, EventSource.AGENT)

        # NOTE: RecallActions don't need an ErrorObservation upon reset, as long as they have no tool calls

        # reset the pending action, this will be called when the agent is STOPPED or ERROR
        self._pending_action = None
        self.agent.reset()