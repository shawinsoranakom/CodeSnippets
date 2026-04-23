def _init_history(self, event_stream: EventStream) -> None:
        """Initializes the agent's history from the event stream.

        The history is a list of events that:
        - Excludes events of types listed in self.filter_out
        - Excludes events with hidden=True attribute
        - For delegate events (between AgentDelegateAction and AgentDelegateObservation):
            - Excludes all events between the action and observation
            - Includes the delegate action and observation themselves
        """
        # define range of events to fetch
        # delegates start with a start_id and initially won't find any events
        # otherwise we're restoring a previous session
        start_id = self.state.start_id if self.state.start_id >= 0 else 0
        end_id = (
            self.state.end_id
            if self.state.end_id >= 0
            else event_stream.get_latest_event_id()
        )

        # sanity check
        if start_id > end_id + 1:
            logger.warning(
                f'start_id {start_id} is greater than end_id + 1 ({end_id + 1}). History will be empty.',
            )
            self.state.history = []
            return

        events: list[Event] = []

        # Get rest of history
        events_to_add = list(
            event_stream.search_events(
                start_id=start_id,
                end_id=end_id,
                reverse=False,
                filter=self.agent_history_filter,
            )
        )
        events.extend(events_to_add)

        # Find all delegate action/observation pairs
        delegate_ranges: list[tuple[int, int]] = []
        delegate_action_ids: list[int] = []  # stack of unmatched delegate action IDs

        for event in events:
            if isinstance(event, AgentDelegateAction):
                delegate_action_ids.append(event.id)
                # Note: we can get agent=event.agent and task=event.inputs.get('task','')
                # if we need to track these in the future

            elif isinstance(event, AgentDelegateObservation):
                # Match with most recent unmatched delegate action
                if not delegate_action_ids:
                    logger.warning(
                        f'Found AgentDelegateObservation without matching action at id={event.id}',
                    )
                    continue

                action_id = delegate_action_ids.pop()
                delegate_ranges.append((action_id, event.id))

        # Filter out events between delegate action/observation pairs
        if delegate_ranges:
            filtered_events: list[Event] = []
            current_idx = 0

            for start_id, end_id in sorted(delegate_ranges):
                # Add events before delegate range
                filtered_events.extend(
                    event for event in events[current_idx:] if event.id < start_id
                )

                # Add delegate action and observation
                filtered_events.extend(
                    event for event in events if event.id in (start_id, end_id)
                )

                # Update index to after delegate range
                current_idx = next(
                    (i for i, e in enumerate(events) if e.id > end_id), len(events)
                )

            # Add any remaining events after last delegate range
            filtered_events.extend(events[current_idx:])

            self.state.history = filtered_events
        else:
            self.state.history = events

        # make sure history is in sync
        self.state.start_id = start_id