def get_events(
        self, start_date: datetime, end_date: datetime | None = None
    ) -> list[CalendarEvent]:
        """Get dailies and recurrences for a given period or the next upcoming."""

        # we only have dailies for today and future recurrences
        if end_date and end_date < self.start_of_today:
            return []
        start_date = max(start_date, self.start_of_today)

        events = []
        for task in self.coordinator.data.tasks:
            #  only dailies that that are not 'grey dailies'
            if not (task.Type is TaskType.DAILY and task.everyX):
                continue
            if task.frequency is Frequency.WEEKLY and not any(
                asdict(task.repeat).values()
            ):
                continue

            recurrences = build_rrule(task)
            recurrence_dates = self.get_recurrence_dates(
                recurrences, start_date, end_date
            )
            for recurrence in recurrence_dates:
                is_future_event = recurrence > self.start_of_today
                is_current_event = (
                    recurrence <= self.start_of_today and not task.completed
                )

                if not is_future_event and not is_current_event:
                    continue
                if TYPE_CHECKING:
                    assert task.text
                    assert task.id
                events.append(
                    CalendarEvent(
                        start=recurrence.date(),
                        end=self.end_date(recurrence, end_date),
                        summary=task.text,
                        description=task.notes,
                        uid=str(task.id),
                        rrule=get_recurrence_rule(recurrences),
                    )
                )
        return sorted(
            events,
            key=lambda event: (
                event.start,
                self.coordinator.data.user.tasksOrder.dailys.index(UUID(event.uid)),
            ),
        )