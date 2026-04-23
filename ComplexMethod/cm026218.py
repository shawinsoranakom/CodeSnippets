async def async_get_events(
        self, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        """Get all tasks in a specific time frame."""
        tasks = self._coordinator.data
        if self._id is None:
            project_task_data = [
                task for task in tasks if self.create_todoist_task(task) is not None
            ]
        else:
            project_task_data = [task for task in tasks if task.project_id == self._id]

        events = []
        for task in project_task_data:
            if task.due is None:
                continue
            start = parse_due_date(task.due)
            if start is None:
                continue
            event = CalendarEvent(
                summary=task.content,
                start=start,
                end=start + timedelta(days=1),
            )
            if (
                event.start_datetime_local is not None
                and event.start_datetime_local >= end_date
            ):
                continue
            if (
                event.end_datetime_local is not None
                and event.end_datetime_local < start_date
            ):
                continue
            events.append(event)
        return events