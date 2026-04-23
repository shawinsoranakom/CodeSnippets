def should_step(self, event: Event) -> bool:
        """Whether the agent should take a step based on an event.

        In general, the agent should take a step if it receives a message from the user,
        or observes something in the environment (after acting).
        """
        # it might be the delegate's day in the sun
        if self.delegate is not None:
            return False

        if isinstance(event, Action):
            if isinstance(event, MessageAction) and event.source == EventSource.USER:
                return True
            if (
                isinstance(event, MessageAction)
                and self.get_agent_state() != AgentState.AWAITING_USER_INPUT
            ):
                # TODO: this is fragile, but how else to check if eligible?
                return True
            if isinstance(event, AgentDelegateAction):
                return True
            if isinstance(event, CondensationAction):
                return True
            if isinstance(event, CondensationRequestAction):
                return True
            return False
        if isinstance(event, Observation):
            if (
                isinstance(event, NullObservation)
                and event.cause is not None
                and event.cause
                > 0  # NullObservation has cause > 0 (RecallAction), not 0 (user message)
            ):
                return True
            if isinstance(event, AgentStateChangedObservation) or isinstance(
                event, NullObservation
            ):
                return False
            return True
        return False