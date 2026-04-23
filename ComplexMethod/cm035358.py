def _add_system_message(self):
        for event in self.event_stream.search_events(start_id=self.state.start_id):
            if isinstance(event, MessageAction) and event.source == EventSource.USER:
                # FIXME: Remove this after 6/1/2025
                # Do not try to add a system message if we first run into
                # a user message -- this means the eventstream exits before
                # SystemMessageAction is introduced.
                # We expect *agent* to handle this case gracefully.
                return

            if isinstance(event, SystemMessageAction):
                # Do not try to add the system message if it already exists
                return

        # Add the system message to the event stream
        # This should be done for all agents, including delegates
        system_message = self.agent.get_system_message()
        if system_message and system_message.content:
            preview = (
                system_message.content[:50] + '...'
                if len(system_message.content) > 50
                else system_message.content
            )
            logger.debug(f'System message: {preview}')
            self.event_stream.add_event(system_message, EventSource.AGENT)