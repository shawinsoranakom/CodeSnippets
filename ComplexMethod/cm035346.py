def from_events(events: list[Event]) -> View:
        """Create a view from a list of events, respecting the semantics of any condensation events."""
        forgotten_event_ids: set[int] = set()
        for event in events:
            if isinstance(event, CondensationAction):
                forgotten_event_ids.update(event.forgotten)
                # Make sure we also forget the condensation action itself
                forgotten_event_ids.add(event.id)
            if isinstance(event, CondensationRequestAction):
                forgotten_event_ids.add(event.id)

        kept_events = [event for event in events if event.id not in forgotten_event_ids]

        # If we have a summary, insert it at the specified offset.
        summary: str | None = None
        summary_offset: int | None = None

        # The relevant summary is always in the last condensation event (i.e., the most recent one).
        for event in reversed(events):
            if isinstance(event, CondensationAction):
                if event.summary is not None and event.summary_offset is not None:
                    summary = event.summary
                    summary_offset = event.summary_offset
                    break

        if summary is not None and summary_offset is not None:
            logger.info(f'Inserting summary at offset {summary_offset}')

            kept_events.insert(
                summary_offset, AgentCondensationObservation(content=summary)
            )

        # Check for an unhandled condensation request -- these are events closer to the
        # end of the list than any condensation action.
        unhandled_condensation_request = False
        for event in reversed(events):
            if isinstance(event, CondensationAction):
                break
            if isinstance(event, CondensationRequestAction):
                unhandled_condensation_request = True
                break

        return View(
            events=kept_events,
            unhandled_condensation_request=unhandled_condensation_request,
            forgotten_event_ids=forgotten_event_ids,
        )