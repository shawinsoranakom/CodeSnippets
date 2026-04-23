async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        """Get all events in a specific time frame."""
        if not self.coordinator.data:
            raise HomeAssistantError("No events scheduled")
        schedule = self.coordinator.data
        event_list: list[CalendarEvent] = []

        for run in schedule:
            event_start = dt_util.as_local(
                dt_util.parse_datetime(run[KEY_START_TIME], raise_on_error=True)
            )
            if event_start > end_date:
                break
            if run[KEY_SKIPPABLE]:  # Future events
                event_end = event_start + timedelta(
                    seconds=int(run[KEY_TOTAL_RUN_DURATION])
                )
            else:  # Past events
                event_end = event_start + timedelta(
                    seconds=int(run[KEY_RUN_SUMMARIES][0][KEY_DURATION_SECONDS])
                )

            if (
                event_end > start_date
                and event_start < end_date
                and KEY_SKIP not in run[KEY_RUN_SUMMARIES][0]
            ):
                valves = ", ".join(
                    [event[KEY_VALVE_NAME] for event in run[KEY_RUN_SUMMARIES]]
                )
                event = CalendarEvent(
                    summary=run[KEY_PROGRAM_NAME],
                    start=event_start,
                    end=event_end,
                    description=valves,
                    uid=f"{run[KEY_PROGRAM_ID]}/{run[KEY_START_TIME]}",
                )
                event_list.append(event)
        return event_list