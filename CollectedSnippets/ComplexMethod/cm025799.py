def build_rrule(task: TaskData) -> rrule:
    """Build rrule string."""

    if TYPE_CHECKING:
        assert task.frequency
        assert task.everyX
    rrule_frequency = FREQUENCY_MAP.get(task.frequency, DAILY)
    weekdays = [day for key, day in WEEKDAY_MAP.items() if getattr(task.repeat, key)]
    bymonthday = (
        task.daysOfMonth if rrule_frequency == MONTHLY and task.daysOfMonth else None
    )

    bysetpos = None
    if rrule_frequency == MONTHLY and task.weeksOfMonth:
        bysetpos = [i + 1 for i in task.weeksOfMonth]
        weekdays = weekdays or [MO]

    return rrule(
        freq=rrule_frequency,
        interval=task.everyX,
        dtstart=dt_util.start_of_local_day(task.startDate),
        byweekday=weekdays if rrule_frequency in [WEEKLY, MONTHLY] else None,
        bymonthday=bymonthday,
        bysetpos=bysetpos,
    )