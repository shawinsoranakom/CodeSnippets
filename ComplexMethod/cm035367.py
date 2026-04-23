async def set_agent_state_to(self, new_state: AgentState) -> None:
        """Updates the agent's state and handles side effects. Can emit events to the event stream.

        Args:
            new_state (AgentState): The new state to set for the agent.
        """
        self.log(
            'info',
            f'Setting agent({self.agent.name}) state from {self.state.agent_state} to {new_state}',
        )

        if new_state == self.state.agent_state:
            return

        # Store old state for control limits check
        old_state = self.state.agent_state

        # Update agent state BEFORE calling _reset() so _reset() sees the correct state
        self.state.agent_state = new_state

        if new_state in (AgentState.STOPPED, AgentState.ERROR):
            self._reset()

        # User is allowing to check control limits and expand them if applicable
        if old_state == AgentState.ERROR and new_state == AgentState.RUNNING:
            self.state_tracker.maybe_increase_control_flags_limits(self.headless_mode)

        if self._pending_action is not None and (
            new_state in (AgentState.USER_CONFIRMED, AgentState.USER_REJECTED)
        ):
            if hasattr(self._pending_action, 'thought'):
                self._pending_action.thought = ''  # type: ignore[union-attr]
            if new_state == AgentState.USER_CONFIRMED:
                confirmation_state = ActionConfirmationStatus.CONFIRMED
            else:
                confirmation_state = ActionConfirmationStatus.REJECTED
            self._pending_action.confirmation_state = confirmation_state  # type: ignore[attr-defined]
            self._pending_action._id = None  # type: ignore[attr-defined]
            self.event_stream.add_event(self._pending_action, EventSource.AGENT)

        # Create observation with reason field if it's an error state
        reason = ''
        if new_state == AgentState.ERROR:
            reason = self.state.last_error

        self.event_stream.add_event(
            AgentStateChangedObservation('', self.state.agent_state, reason),
            EventSource.ENVIRONMENT,
        )

        # Save state whenever agent state changes to ensure we don't lose state
        # in case of crashes or unexpected circumstances
        self.save_state()