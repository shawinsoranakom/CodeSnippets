def get_condensation(self, view: View) -> Condensation:
        head = view[: self.keep_first]
        target_size = self.max_size // 2
        # Number of events to keep from the tail -- target size, minus however many
        # prefix events from the head, minus one for the summarization event
        events_from_tail = target_size - len(head) - 1

        summary_event = (
            view[self.keep_first]
            if isinstance(view[self.keep_first], AgentCondensationObservation)
            else AgentCondensationObservation('No events summarized')
        )

        # Identify events to be forgotten (those not in head or tail)
        forgotten_events = []
        for event in view[self.keep_first : -events_from_tail]:
            if not isinstance(event, AgentCondensationObservation):
                forgotten_events.append(event)

        # Construct prompt for summarization
        prompt = """You are maintaining a context-aware state summary for an interactive software agent. This summary is critical because it:
1. Preserves essential context when conversation history grows too large
2. Prevents lost work when the session length exceeds token limits
3. Helps maintain continuity across multiple interactions

You will be given:
- A list of events (actions taken by the agent)
- The most recent previous summary (if one exists)

Capture all relevant information, especially:
- User requirements that were explicitly stated
- Work that has been completed
- Tasks that remain pending
- Current state of code, variables, and data structures
- The status of any version control operations"""

        prompt += '\n\n'

        # Add the previous summary if it exists. We'll always have a summary
        # event, but the types aren't precise enought to guarantee that it has a
        # message attribute.
        summary_event_content = self._truncate(
            summary_event.message if summary_event.message else ''
        )
        prompt += f'<PREVIOUS SUMMARY>\n{summary_event_content}\n</PREVIOUS SUMMARY>\n'

        prompt += '\n\n'

        # Add all events that are being forgotten. We use the string
        # representation defined by the event, and truncate it if necessary.
        for forgotten_event in forgotten_events:
            event_content = self._truncate(str(forgotten_event))
            prompt += f'<EVENT id={forgotten_event.id}>\n{event_content}\n</EVENT>\n'

        messages = [Message(role='user', content=[TextContent(text=prompt)])]

        response = self.llm.completion(
            messages=self.llm.format_messages_for_llm(messages),
            tools=[StateSummary.tool_description()],
            tool_choice={
                'type': 'function',
                'function': {'name': 'create_state_summary'},
            },
        )

        try:
            # Extract the message containing tool calls
            message = response.choices[0].message

            # Check if there are tool calls
            if not hasattr(message, 'tool_calls') or not message.tool_calls:
                raise ValueError('No tool calls found in response')

            # Find the create_state_summary tool call
            summary_tool_call = None
            for tool_call in message.tool_calls:
                if tool_call.function.name == 'create_state_summary':
                    summary_tool_call = tool_call
                    break

            if not summary_tool_call:
                raise ValueError('create_state_summary tool call not found')

            # Parse the arguments
            args_json = summary_tool_call.function.arguments
            args_dict = json.loads(args_json)

            # Create a StateSummary object
            summary = StateSummary.model_validate(args_dict)

        except (ValueError, AttributeError, KeyError, json.JSONDecodeError) as e:
            logger.warning(
                f'Failed to parse summary tool call: {e}. Using empty summary.'
            )
            summary = StateSummary()

        self.add_metadata('response', response.model_dump())
        self.add_metadata('metrics', self.llm.metrics.get())

        return Condensation(
            action=CondensationAction(
                forgotten_events_start_id=min(event.id for event in forgotten_events),
                forgotten_events_end_id=max(event.id for event in forgotten_events),
                summary=str(summary),
                summary_offset=self.keep_first,
            )
        )