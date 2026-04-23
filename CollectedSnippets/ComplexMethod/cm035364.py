async def _handle_observation(self, observation: Observation) -> None:
        """Handles observation from the event stream.

        Args:
            observation (observation): The observation to handle.
        """
        observation_to_print = copy.deepcopy(observation)
        if len(observation_to_print.content) > self.agent.llm.config.max_message_chars:
            observation_to_print.content = truncate_content(
                observation_to_print.content, self.agent.llm.config.max_message_chars
            )
        # Use info level if LOG_ALL_EVENTS is set
        log_level = 'info' if os.getenv('LOG_ALL_EVENTS') in ('true', '1') else 'debug'
        self.log(
            log_level, str(observation_to_print), extra={'msg_type': 'OBSERVATION'}
        )

        # this happens for runnable actions and microagent actions
        if self._pending_action and self._pending_action.id == observation.cause:
            if self.state.agent_state == AgentState.AWAITING_USER_CONFIRMATION:
                return

            self._pending_action = None

            if self.state.agent_state == AgentState.USER_CONFIRMED:
                await self.set_agent_state_to(AgentState.RUNNING)
            if self.state.agent_state == AgentState.USER_REJECTED:
                await self.set_agent_state_to(AgentState.AWAITING_USER_INPUT)
            return