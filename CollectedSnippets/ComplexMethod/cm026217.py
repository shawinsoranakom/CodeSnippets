def select_best_task(project_tasks: list[TodoistEvent]) -> TodoistEvent:
        """Search through a list of events for the "best" event to select.

        The "best" event is determined by the following criteria:
          * A proposed event must not be completed
          * A proposed event must have an end date (otherwise we go with
            the event at index 0, selected above)
          * A proposed event must be on the same day or earlier as our
            current event
          * If a proposed event is an earlier day than what we have so
            far, select it
          * If a proposed event is on the same day as our current event
            and the proposed event has a higher priority than our current
            event, select it
          * If a proposed event is on the same day as our current event,
            has the same priority as our current event, but is due earlier
            in the day, select it
        """
        # Start at the end of the list, so if tasks don't have a due date
        # the newest ones are the most important.

        event = project_tasks[-1]

        for proposed_event in project_tasks:
            if event == proposed_event:
                continue

            if proposed_event[COMPLETED]:
                # Event is complete!
                continue

            if proposed_event[END] is None:
                # No end time:
                if event[END] is None and (proposed_event[PRIORITY] < event[PRIORITY]):
                    # They also have no end time,
                    # but we have a higher priority.
                    event = proposed_event
                continue

            if event[END] is None:
                # We have an end time, they do not.
                event = proposed_event
                continue

            if proposed_event[END].date() > event[END].date():
                # Event is too late.
                continue

            if proposed_event[END].date() < event[END].date():
                # Event is earlier than current, select it.
                event = proposed_event
                continue

            if proposed_event[PRIORITY] > event[PRIORITY]:
                # Proposed event has a higher priority.
                event = proposed_event
                continue

            if proposed_event[PRIORITY] == event[PRIORITY] and (
                event[END] is not None and proposed_event[END] < event[END]
            ):
                event = proposed_event
                continue
        return event