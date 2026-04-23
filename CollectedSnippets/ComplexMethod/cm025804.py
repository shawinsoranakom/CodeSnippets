def get_events(
        self, start_date: datetime, end_date: datetime | None = None
    ) -> list[CalendarEvent]:
        """Reminders for todos."""

        events = []

        for task in self.coordinator.data.tasks:
            if task.Type is not TaskType.TODO or task.completed:
                continue

            for reminder in task.reminders:
                # reminders are returned by the API in local time but with wrong
                # timezone (UTC) and arbitrary added seconds/microseconds. When
                # creating reminders in Habitica only hours and minutes can be defined.
                start = reminder.time.replace(
                    tzinfo=dt_util.DEFAULT_TIME_ZONE, second=0, microsecond=0
                )
                end = start + timedelta(hours=1)

                if end < start_date:
                    # Event ends before date range
                    continue

                if end_date and start > end_date:
                    # Event starts after date range
                    continue
                if TYPE_CHECKING:
                    assert task.text
                    assert task.id
                events.append(
                    CalendarEvent(
                        start=start,
                        end=end,
                        summary=task.text,
                        description=task.notes,
                        uid=f"{task.id}_{reminder.id}",
                    )
                )

        return sorted(
            events,
            key=lambda event: event.start,
        )