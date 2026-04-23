def _attendance_intervals_batch(self, start_dt, end_dt, resources=None, domain=None, tz=None, lunch=False):
        assert start_dt.tzinfo and end_dt.tzinfo
        self.ensure_one()
        if not resources:
            resources = self.env['resource.resource']
            resources_list = [resources]
        else:
            resources_list = list(resources) + [self.env['resource.resource']]

        if self.flexible_hours and lunch:
            return {resource.id: Intervals([], keep_distinct=True) for resource in resources_list}

        domain = Domain.AND([
            Domain(domain or Domain.TRUE),
            Domain('calendar_id', '=', self.id),
            Domain('display_type', '=', False),
            Domain('day_period', '!=' if not lunch else '=', 'lunch'),
        ])

        attendances = self.env['resource.calendar.attendance'].search(domain)
        # Since we only have one calendar to take in account
        # Group resources per tz they will all have the same result
        resources_per_tz = defaultdict(list)
        for resource in resources_list:
            resources_per_tz[tz or timezone((resource or self).tz)].append(resource)
        # Resource specific attendances
        # Calendar attendances per day of the week
        # * 7 days per week * 2 for two week calendars
        attendances_per_day = [self.env['resource.calendar.attendance']] * 7 * 2
        weekdays = set()
        for attendance in attendances:
            weekday = int(attendance.dayofweek)
            weekdays.add(weekday)
            if self.two_weeks_calendar:
                weektype = int(attendance.week_type)
                attendances_per_day[weekday + 7 * weektype] |= attendance
            else:
                attendances_per_day[weekday] |= attendance
                attendances_per_day[weekday + 7] |= attendance

        start = start_dt.astimezone(utc)
        end = end_dt.astimezone(utc)
        bounds_per_tz = {
            tz: (start_dt.astimezone(tz), end_dt.astimezone(tz))
            for tz in resources_per_tz
        }
        # Use the outer bounds from the requested timezones
        for low, high in bounds_per_tz.values():
            start = min(start, low.replace(tzinfo=utc))
            end = max(end, high.replace(tzinfo=utc))
        # Generate once with utc as timezone
        days = rrule(DAILY, start.date(), until=end.date(), byweekday=weekdays)
        ResourceCalendarAttendance = self.env['resource.calendar.attendance']
        base_result = []
        for day in days:
            week_type = ResourceCalendarAttendance.get_week_type(day)
            attendances = attendances_per_day[day.weekday() + 7 * week_type]
            for attendance in attendances:
                day_from = datetime.combine(day, float_to_time(attendance.hour_from))
                day_to = datetime.combine(day, float_to_time(attendance.hour_to))
                base_result.append((day_from, day_to, attendance))

        # Copy the result localized once per necessary timezone
        # Strictly speaking comparing start_dt < time or start_dt.astimezone(tz) < time
        # should always yield the same result. however while working with dates it is easier
        # if all dates have the same format
        result_per_tz = {
            tz: [(max(bounds_per_tz[tz][0], tz.localize(val[0])),
                min(bounds_per_tz[tz][1], tz.localize(val[1])),
                val[2])
                    for val in base_result]
            for tz in resources_per_tz
        }
        resource_calendars = resources._get_calendar_at(start_dt, tz)
        result_per_resource_id = dict()
        for tz, tz_resources in resources_per_tz.items():
            res = result_per_tz[tz]

            res_intervals = Intervals(res, keep_distinct=True)
            start_datetime = start_dt.astimezone(tz)
            end_datetime = end_dt.astimezone(tz)

            for resource in tz_resources:
                if resource and not resource_calendars.get(resource, False):
                    # If the resource is fully flexible, return the whole period from start_dt to end_dt with a dummy attendance
                    hours = (end_dt - start_dt).total_seconds() / 3600
                    days = hours / 24
                    dummy_attendance = self.env['resource.calendar.attendance'].new({
                        'duration_hours': hours,
                        'duration_days': days,
                    })
                    result_per_resource_id[resource.id] = Intervals([(start_datetime, end_datetime, dummy_attendance)], keep_distinct=True)
                elif self.flexible_hours or (resource and resource_calendars[resource].flexible_hours):
                    # For flexible Calendars, we create intervals to fill in the weekly intervals with the average daily hours
                    # until the full time required hours are met. This gives us the most correct approximation when looking at a daily
                    # and weekly range for time offs and overtime calculations and work entry generation
                    start_date = start_datetime
                    end_datetime_adjusted = end_datetime - relativedelta(seconds=1)
                    end_date = end_datetime_adjusted

                    calendar = resource_calendars[resource] if resource else self

                    max_hours_per_week = calendar.hours_per_week
                    max_hours_per_day = calendar.hours_per_day

                    intervals = []
                    current_start_day = start_date

                    while current_start_day <= end_date:
                        current_end_of_week = current_start_day + timedelta(days=6)

                        week_start = max(current_start_day, start_date)
                        week_end = min(current_end_of_week, end_date)

                        if current_start_day < start_date:
                            prior_days = (start_date - current_start_day).days
                            prior_hours = min(max_hours_per_week, max_hours_per_day * prior_days)
                        else:
                            prior_hours = 0

                        remaining_hours = max(0, max_hours_per_week - prior_hours)
                        remaining_hours = min(remaining_hours, (end_dt - start_dt).total_seconds() / 3600)

                        current_day = week_start
                        while current_day <= week_end:
                            if remaining_hours > 0:
                                day_start = tz.localize(datetime.combine(current_day, time.min))
                                day_end = tz.localize(datetime.combine(current_day, time.max))
                                day_period_start = max(start_datetime, day_start)
                                day_period_end = min(end_datetime, day_end)
                                allocate_hours = min(max_hours_per_day, remaining_hours, (day_period_end - day_period_start).total_seconds() / 3600)
                                remaining_hours -= allocate_hours

                                # Create interval centered at 12:00 PM (or as close as possible)
                                midpoint = tz.localize(datetime.combine(current_day, time(12, 0)))
                                start_time = midpoint - timedelta(hours=allocate_hours / 2)
                                end_time = midpoint + timedelta(hours=allocate_hours / 2)

                                if start_time < day_period_start:
                                    start_time = day_period_start
                                    end_time = start_time + timedelta(hours=allocate_hours)
                                elif end_time > day_period_end:
                                    end_time = day_period_end
                                    start_time = end_time - timedelta(hours=allocate_hours)

                                dummy_attendance = self.env['resource.calendar.attendance'].new({
                                    'duration_hours': allocate_hours,
                                    'duration_days': 1,
                                })

                                intervals.append((start_time, end_time, dummy_attendance))

                            current_day += timedelta(days=1)

                        current_start_day += timedelta(days=7)

                    result_per_resource_id[resource.id] = Intervals(intervals, keep_distinct=True)
                else:
                    result_per_resource_id[resource.id] = res_intervals
        return result_per_resource_id