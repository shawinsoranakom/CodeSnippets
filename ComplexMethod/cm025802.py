def get_events(
        self, start_date: datetime, end_date: datetime | None = None
    ) -> list[CalendarEvent]:
        """Get all dated todos."""

        events = []
        for task in self.coordinator.data.tasks:
            if not (
                task.Type is TaskType.TODO
                and not task.completed
                and task.date is not None  # only if has due date
            ):
                continue

            start = dt_util.start_of_local_day(task.date)
            end = start + timedelta(days=1)
            # return current and upcoming events or events within the requested range

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
                    start=start.date(),
                    end=end.date(),
                    summary=task.text,
                    description=task.notes,
                    uid=str(task.id),
                )
            )
        return sorted(
            events,
            key=lambda event: (
                event.start,
                self.coordinator.data.user.tasksOrder.todos.index(UUID(event.uid)),
            ),
        )