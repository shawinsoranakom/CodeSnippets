def __init__(
        self,
        participants: List[ChatAgent],
        *,
        name: str | None = None,
        description: str | None = None,
        termination_condition: TerminationCondition | None = None,
        max_turns: int | None = None,
        runtime: AgentRuntime | None = None,
        custom_message_types: List[type[BaseAgentEvent | BaseChatMessage]] | None = None,
        emit_team_events: bool = False,
    ) -> None:
        for participant in participants:
            if not isinstance(participant, ChatAgent):
                raise TypeError(f"Participant {participant} must be a ChatAgent.")
        super().__init__(
            name=name or self.DEFAULT_NAME,
            description=description or self.DEFAULT_DESCRIPTION,
            participants=[participant for participant in participants],
            group_chat_manager_name="SwarmGroupChatManager",
            group_chat_manager_class=SwarmGroupChatManager,
            termination_condition=termination_condition,
            max_turns=max_turns,
            runtime=runtime,
            custom_message_types=custom_message_types,
            emit_team_events=emit_team_events,
        )
        # The first participant must be able to produce handoff messages.
        first_participant = self._participants[0]
        assert isinstance(first_participant, ChatAgent)
        if HandoffMessage not in first_participant.produced_message_types:
            raise ValueError("The first participant must be able to produce a handoff messages.")