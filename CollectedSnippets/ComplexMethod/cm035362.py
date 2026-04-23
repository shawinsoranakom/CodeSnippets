async def _on_event(self, event: Event) -> None:
        if hasattr(event, 'hidden') and event.hidden:
            return

        self.state_tracker.add_history(event)

        if isinstance(event, Action):
            await self._handle_action(event)
        elif isinstance(event, Observation):
            await self._handle_observation(event)

        should_step = self.should_step(event)
        if should_step:
            self.log(
                'debug',
                f'Stepping agent after event: {type(event).__name__}',
                extra={'msg_type': 'STEPPING_AGENT'},
            )
            await self._step_with_exception_handling()
        elif isinstance(event, MessageAction) and event.source == EventSource.USER:
            # If we received a user message but aren't stepping, log why
            self.log(
                'warning',
                f'Not stepping agent after user message. Current state: {self.get_agent_state()}',
                extra={'msg_type': 'NOT_STEPPING_AFTER_USER_MESSAGE'},
            )