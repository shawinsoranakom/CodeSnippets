def _get_hours_for_date(self, target_date, day_period=None):
        """
        An instance method on a calendar to get the start and end float hours for a given date.
        :param target_date: The date to find working hours.
        :param day_period: Optional string ('morning', 'afternoon') to filter for half-days.
        :return: A tuple of floats (hour_from, hour_to).
        """
        self.ensure_one()
        if not target_date:
            err = "Target Date cannot be empty"
            raise ValueError(err)
        if self.flexible_hours:
            # Quick calculation to center flexible hours around 12PM midday
            datetimes = [12.0 - self.hours_per_day / 2.0, 12.0, 12.0 + self.hours_per_day / 2.0]
            if day_period:
                return (datetimes[0], datetimes[1]) if day_period == 'morning' else (datetimes[1], datetimes[2])
            return (datetimes[0], datetimes[2])

        domain = [
            ('calendar_id', '=', self.id),
            ('display_type', '=', False),
            ('day_period', '!=', 'lunch'),
        ]

        init_attendances = self.env['resource.calendar.attendance']._read_group(domain=domain,
        groupby=['week_type', 'dayofweek', 'day_period'],
        aggregates=['hour_from:min', 'hour_to:max'],
        order='dayofweek,hour_from:min')

        init_attendances = [DummyAttendance(hour_from, hour_to, dayofweek, day_period, week_type)
            for week_type, dayofweek, day_period, hour_from, hour_to in init_attendances]

        if day_period:
            attendances = [att for att in init_attendances if att.day_period == day_period]
            for attendance in filter(lambda att: att.day_period == 'full_day', init_attendances):
                # Split full-day attendances at their midpoint.
                half_time = (attendance.hour_from + attendance.hour_to) / 2
                attendances.append(attendance._replace(
                    hour_from=attendance.hour_from if day_period == 'morning' else half_time,
                    hour_to=attendance.hour_to if day_period == 'afternoon' else half_time,
                ))

        else:
            attendances = init_attendances

        default_start = min((att.hour_from for att in attendances), default=0.0)
        default_end = max((att.hour_to for att in attendances), default=0.0)

        week_type = False
        if self.two_weeks_calendar:
            week_type = str(self.env['resource.calendar.attendance'].get_week_type(target_date))

        filtered_attendances = [att for att in attendances if att.week_type == week_type and int(att.dayofweek) == target_date.weekday()]
        hour_from = min((att.hour_from for att in filtered_attendances), default=default_start)
        hour_to = max((att.hour_to for att in filtered_attendances), default=default_end)

        return (hour_from, hour_to)