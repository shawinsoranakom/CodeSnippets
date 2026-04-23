def resolve_period(
    period_def: StatisticPeriod,
) -> tuple[datetime | None, datetime | None]:
    """Return start and end datetimes for a statistic period definition."""
    start_time = None
    end_time = None

    if "calendar" in period_def:
        calendar_period = period_def["calendar"]["period"]
        start_of_day = dt_util.start_of_local_day()
        cal_offset = period_def["calendar"].get("offset", 0)
        if calendar_period == "hour":
            start_time = dt_util.now().replace(minute=0, second=0, microsecond=0)
            start_time += timedelta(hours=cal_offset)
            end_time = start_time + timedelta(hours=1)
        elif calendar_period == "day":
            start_time = start_of_day
            start_time += timedelta(days=cal_offset)
            end_time = start_time + timedelta(days=1)
        elif calendar_period == "week":
            first_weekday = WEEKDAYS.index(
                period_def["calendar"].get("first_weekday", WEEKDAYS[0])
            )
            start_time = start_of_day - timedelta(
                days=(start_of_day.weekday() - first_weekday) % 7
            )
            start_time += timedelta(days=cal_offset * 7)
            end_time = start_time + timedelta(weeks=1)
        elif calendar_period == "month":
            month_now = start_of_day.month
            new_month = (month_now - 1 + cal_offset) % 12 + 1
            new_year = start_of_day.year + (month_now - 1 + cal_offset) // 12
            start_time = start_of_day.replace(year=new_year, month=new_month, day=1)
            end_time = (start_time + timedelta(days=31)).replace(day=1)
        else:  # calendar_period = "year"
            start_time = start_of_day.replace(
                year=start_of_day.year + cal_offset, month=1, day=1
            )
            end_time = (start_time + timedelta(days=366)).replace(day=1)

        start_time = dt_util.as_utc(start_time)
        end_time = dt_util.as_utc(end_time)

    elif "fixed_period" in period_def:
        start_time = period_def["fixed_period"].get("start_time")
        end_time = period_def["fixed_period"].get("end_time")

    elif "rolling_window" in period_def:
        duration = period_def["rolling_window"]["duration"]
        now = dt_util.utcnow()
        start_time = now - duration
        end_time = start_time + duration

        if offset := period_def["rolling_window"].get("offset"):
            start_time += offset
            end_time += offset

    return (start_time, end_time)