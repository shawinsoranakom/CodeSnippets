def next_due_date(task: TaskData, today: datetime.datetime) -> datetime.date | None:
    """Calculate due date for dailies and yesterdailies."""

    if task.everyX == 0 or not task.nextDue:  # grey dailies never become due
        return None
    if task.frequency is Frequency.WEEKLY and not any(asdict(task.repeat).values()):
        return None

    if TYPE_CHECKING:
        assert task.startDate

    if task.isDue is True and not task.completed:
        return dt_util.as_local(today).date()

    if task.startDate > today:
        if task.frequency is Frequency.DAILY or (
            task.frequency in (Frequency.MONTHLY, Frequency.YEARLY) and task.daysOfMonth
        ):
            return dt_util.as_local(task.startDate).date()

        if (
            task.frequency in (Frequency.WEEKLY, Frequency.MONTHLY)
            and (nextdue := task.nextDue[0])
            and task.startDate > nextdue
        ):
            return dt_util.as_local(task.nextDue[1]).date()

    return dt_util.as_local(task.nextDue[0]).date()