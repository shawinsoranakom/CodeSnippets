def process_events(
        self,
        condensed_history: list[Event],
        initial_user_action: MessageAction,
        forgotten_event_ids: set[int] | None = None,
        max_message_chars: int | None = None,
        vision_is_active: bool = False,
    ) -> list[Message]:
        """Process state history into a list of messages for the LLM.

        Ensures that tool call actions are processed correctly in function calling mode.

        Args:
            condensed_history: The condensed history of events to convert
            initial_user_action: The initial user message action, if available. Used to ensure the conversation starts correctly.
            forgotten_event_ids: Set of event IDs that have been forgotten/condensed. If the initial user action's ID
                is in this set, it will not be re-inserted to prevent re-execution of old instructions.
            max_message_chars: The maximum number of characters in the content of an event included
                in the prompt to the LLM. Larger observations are truncated.
            vision_is_active: Whether vision is active in the LLM. If True, image URLs will be included.
        """
        events = condensed_history
        # Default to empty set if not provided
        if forgotten_event_ids is None:
            forgotten_event_ids = set()

        # Ensure the event list starts with SystemMessageAction, then MessageAction(source='user')
        self._ensure_system_message(events)
        self._ensure_initial_user_message(
            events, initial_user_action, forgotten_event_ids
        )

        # log visual browsing status
        logger.debug(f'Visual browsing: {self.agent_config.enable_som_visual_browsing}')

        # Initialize empty messages list
        messages = []

        # Process regular events
        pending_tool_call_action_messages: dict[str, Message] = {}
        tool_call_id_to_message: dict[str, Message] = {}

        for i, event in enumerate(events):
            # create a regular message from an event
            if isinstance(event, Action):
                messages_to_add = self._process_action(
                    action=event,
                    pending_tool_call_action_messages=pending_tool_call_action_messages,
                    vision_is_active=vision_is_active,
                )
            elif isinstance(event, Observation):
                messages_to_add = self._process_observation(
                    obs=event,
                    tool_call_id_to_message=tool_call_id_to_message,
                    max_message_chars=max_message_chars,
                    vision_is_active=vision_is_active,
                    enable_som_visual_browsing=self.agent_config.enable_som_visual_browsing,
                    current_index=i,
                    events=events,
                )
            else:
                raise ValueError(f'Unknown event type: {type(event)}')

            # Check pending tool call action messages and see if they are complete
            _response_ids_to_remove = []
            for (
                response_id,
                pending_message,
            ) in pending_tool_call_action_messages.items():
                assert pending_message.tool_calls is not None, (
                    'Tool calls should NOT be None when function calling is enabled & the message is considered pending tool call. '
                    f'Pending message: {pending_message}'
                )
                if all(
                    tool_call.id in tool_call_id_to_message
                    for tool_call in pending_message.tool_calls
                ):
                    # If complete:
                    # -- 1. Add the message that **initiated** the tool calls
                    messages_to_add.append(pending_message)
                    # -- 2. Add the tool calls **results***
                    for tool_call in pending_message.tool_calls:
                        messages_to_add.append(tool_call_id_to_message[tool_call.id])
                        tool_call_id_to_message.pop(tool_call.id)
                    _response_ids_to_remove.append(response_id)
            # Cleanup the processed pending tool messages
            for response_id in _response_ids_to_remove:
                pending_tool_call_action_messages.pop(response_id)

            messages += messages_to_add

        # Apply final filtering so that the messages in context don't have unmatched tool calls
        # and tool responses, for example
        messages = list(ConversationMemory._filter_unmatched_tool_calls(messages))

        # Apply final formatting
        messages = self._apply_user_message_formatting(messages)

        return messages