def find_next_time_expression_time(
    now: dt.datetime,  # pylint: disable=redefined-outer-name
    seconds: list[int],
    minutes: list[int],
    hours: list[int],
) -> dt.datetime:
    """Find the next datetime from now for which the time expression matches.

    The algorithm looks at each time unit separately and tries to find the
    next one that matches for each. If any of them would roll over, all
    time units below that are reset to the first matching value.

    Timezones are also handled (the tzinfo of the now object is used),
    including daylight saving time.
    """
    if not seconds or not minutes or not hours:
        raise ValueError("Cannot find a next time: Time expression never matches!")

    while True:
        # Reset microseconds and fold; fold (for ambiguous DST times) will be
        # handled later.
        result = now.replace(microsecond=0, fold=0)

        # Match next second
        if (next_second := _lower_bound(seconds, result.second)) is None:
            # No second to match in this minute. Roll-over to next minute.
            next_second = seconds[0]
            result += dt.timedelta(minutes=1)

        if result.second != next_second:
            result = result.replace(second=next_second)

        # Match next minute
        next_minute = _lower_bound(minutes, result.minute)
        if next_minute != result.minute:
            # We're in the next minute. Seconds needs to be reset.
            result = result.replace(second=seconds[0])

        if next_minute is None:
            # No minute to match in this hour. Roll-over to next hour.
            next_minute = minutes[0]
            result += dt.timedelta(hours=1)

        if result.minute != next_minute:
            result = result.replace(minute=next_minute)

        # Match next hour
        next_hour = _lower_bound(hours, result.hour)
        if next_hour != result.hour:
            # We're in the next hour. Seconds+minutes needs to be reset.
            result = result.replace(second=seconds[0], minute=minutes[0])

        if next_hour is None:
            # No minute to match in this day. Roll-over to next day.
            next_hour = hours[0]
            result += dt.timedelta(days=1)

        if result.hour != next_hour:
            result = result.replace(hour=next_hour)

        if result.tzinfo in (None, UTC):
            # Using UTC, no DST checking needed
            return result

        if not _datetime_exists(result):
            # When entering DST and clocks are turned forward.
            # There are wall clock times that don't "exist" (an hour is skipped).

            # -> trigger on the next time that 1. matches the pattern and 2. does exist
            # for example:
            #   on 2021.03.28 02:00:00 in CET timezone clocks are turned forward an hour
            #   with pattern "02:30", don't run on 28 mar (such a wall time does not
            #   exist on this day) instead run at 02:30 the next day

            # We solve this edge case by just iterating one second until the result
            # exists (max. 3600 operations, which should be fine for an edge case that
            # happens once a year)
            now += dt.timedelta(seconds=1)
            continue

        if not _datetime_ambiguous(now):
            return result

        # When leaving DST and clocks are turned backward.
        # Then there are wall clock times that are ambiguous i.e. exist with DST and
        # without DST. The logic above does not take into account if a given pattern
        # matches _twice_ in a day.
        # Example: on 2021.10.31 02:00:00 in CET timezone clocks are turned
        # backward an hour.

        if _datetime_ambiguous(result):
            # `now` and `result` are both ambiguous, so the next match happens
            # _within_ the current fold.

            # Examples:
            #  1. 2021.10.31 02:00:00+02:00 with pattern 02:30
            #       -> 2021.10.31 02:30:00+02:00
            #  2. 2021.10.31 02:00:00+01:00 with pattern 02:30
            #       -> 2021.10.31 02:30:00+01:00
            return result.replace(fold=now.fold)

        if now.fold == 0:
            # `now` is in the first fold, but result is not ambiguous (meaning it no
            # longer matches within the fold).
            #   -> Check if result matches in the next fold. If so, emit that match

            # Turn back the time by the DST offset, effectively run the algorithm on
            # the first fold. If it matches on the first fold, that means it will also
            # match on the second one.

            # Example: 2021.10.31 02:45:00+02:00 with pattern 02:30
            #   -> 2021.10.31 02:30:00+01:00

            check_result = find_next_time_expression_time(
                now + _dst_offset_diff(now), seconds, minutes, hours
            )
            if _datetime_ambiguous(check_result):
                return check_result.replace(fold=1)

        return result