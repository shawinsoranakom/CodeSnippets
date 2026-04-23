def get_events(
        self, start_date: datetime, end_date: datetime | None = None
    ) -> list[CalendarEvent]:
        """Reminders for dailies."""

        events = []
        if end_date and end_date < self.start_of_today:
            return []
        start_date = max(start_date, self.start_of_today)

        for task in self.coordinator.data.tasks:
            if not (task.Type is TaskType.DAILY and task.everyX):
                continue

            if task.frequency is Frequency.WEEKLY and not any(
                asdict(task.repeat).values()
            ):
                continue

            recurrences = build_rrule(task)
            recurrences_start = self.start_of_today

            recurrence_dates = self.get_recurrence_dates(
                recurrences, recurrences_start, end_date
            )
            for recurrence in recurrence_dates:
                is_future_event = recurrence > self.start_of_today
                is_current_event = (
                    recurrence <= self.start_of_today and not task.completed
                )

                if not is_future_event and not is_current_event:
                    continue

                for reminder in task.reminders:
                    start = self.start(reminder.time, recurrence)
                    end = start + timedelta(hours=1)

                    if end < start_date:
                        # Event ends before date range
                        continue

                    if TYPE_CHECKING:
                        assert task.id
                        assert task.text
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