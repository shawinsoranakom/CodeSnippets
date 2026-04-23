def __init__(
        self,
        name: str,
        description: str,
        participants: List[ChatAgent | Team],
        group_chat_manager_name: str,
        group_chat_manager_class: type[SequentialRoutedAgent],
        termination_condition: TerminationCondition | None = None,
        max_turns: int | None = None,
        runtime: AgentRuntime | None = None,
        custom_message_types: List[type[BaseAgentEvent | BaseChatMessage]] | None = None,
        emit_team_events: bool = False,
    ):
        self._name = name
        self._description = description
        if len(participants) == 0:
            raise ValueError("At least one participant is required.")
        if len(participants) != len(set(participant.name for participant in participants)):
            raise ValueError("The participant names must be unique.")
        self._participants = participants
        self._base_group_chat_manager_class = group_chat_manager_class
        self._termination_condition = termination_condition
        self._max_turns = max_turns
        self._message_factory = MessageFactory()
        if custom_message_types is not None:
            for message_type in custom_message_types:
                self._message_factory.register(message_type)

        for agent in participants:
            if isinstance(agent, ChatAgent):
                for message_type in agent.produced_message_types:
                    try:
                        is_registered = self._message_factory.is_registered(message_type)  # type: ignore[reportUnknownArgumentType]
                        if issubclass(message_type, StructuredMessage) and not is_registered:
                            self._message_factory.register(message_type)  # type: ignore[reportUnknownArgumentType]
                    except TypeError:
                        # Not a class or not a valid subclassable type (skip)
                        pass

        # The team ID is a UUID that is used to identify the team and its participants
        # in the agent runtime. It is used to create unique topic types for each participant.
        # Currently, team ID is binded to an object instance of the group chat class.
        # So if you create two instances of group chat, there will be two teams with different IDs.
        self._team_id = str(uuid.uuid4())

        # Constants for the group chat team.
        # The names are used to identify the agents within the team.
        # The names may not be unique across different teams.
        self._group_chat_manager_name = group_chat_manager_name
        self._participant_names: List[str] = [participant.name for participant in participants]
        self._participant_descriptions: List[str] = [participant.description for participant in participants]
        # The group chat topic type is used for broadcast communication among all participants and the group chat manager.
        self._group_topic_type = f"group_topic_{self._team_id}"
        # The group chat manager topic type is used for direct communication with the group chat manager.
        self._group_chat_manager_topic_type = f"{self._group_chat_manager_name}_{self._team_id}"
        # The participant topic types are used for direct communication with each participant.
        self._participant_topic_types: List[str] = [
            f"{participant.name}_{self._team_id}" for participant in participants
        ]
        # The output topic type is used for emitting streaming messages from the group chat.
        # The group chat manager will relay the messages to the output message queue.
        self._output_topic_type = f"output_topic_{self._team_id}"

        # The queue for collecting the output messages.
        self._output_message_queue: asyncio.Queue[BaseAgentEvent | BaseChatMessage | GroupChatTermination] = (
            asyncio.Queue()
        )

        # Create a runtime for the team.
        if runtime is not None:
            self._runtime = runtime
            self._embedded_runtime = False
        else:
            # Use a embedded single-threaded runtime for the group chat.
            # Background exceptions must not be ignored as it results in non-surfaced exceptions and early team termination.
            self._runtime = SingleThreadedAgentRuntime(ignore_unhandled_exceptions=False)
            self._embedded_runtime = True

        # Flag to track if the group chat has been initialized.
        self._initialized = False

        # Flag to track if the group chat is running.
        self._is_running = False

        # Flag to track if the team events should be emitted.
        self._emit_team_events = emit_team_events