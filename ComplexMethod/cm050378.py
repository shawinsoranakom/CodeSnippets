def _get_flexible_resource_valid_work_intervals(self, start, end):
        if not self:
            return {}, {}, {}

        assert all(record._is_flexible() for record in self)
        assert start.tzinfo and end.tzinfo

        start_day, end_day = start.date(), end.date()
        week_start_date, week_end_date = start, end
        locale = babel_locale_parse(get_lang(self.env).code)
        week_start_date = weekstart(locale, start)
        week_end_date = weekend(locale, end)
        end_year, end_week = weeknumber(locale, week_end_date)

        min_start_date = week_start_date + relativedelta(hour=0, minute=0, second=0, microsecond=0)
        max_end_date = week_end_date + relativedelta(days=1, hour=0, minute=0, second=0, microsecond=0)

        resource_work_intervals = defaultdict(Intervals)
        calendar_resources = defaultdict(lambda: self.env['resource.resource'])

        resource_calendar_validity_intervals = self._get_flexible_resources_calendars_validity_within_period(min_start_date, max_end_date)
        for resource in self:
            # For each resource, retrieve their calendars validity intervals
            for calendar, work_intervals in resource_calendar_validity_intervals[resource.id].items():
                calendar_resources[calendar] |= resource
                resource_work_intervals[resource.id] |= work_intervals

        resource_by_id = {resource.id: resource for resource in self}

        resource_hours_per_day = defaultdict(lambda: defaultdict(float))
        resource_hours_per_week = defaultdict(lambda: defaultdict(float))
        locale = get_lang(self.env).code

        for resource in self:
            if resource._is_fully_flexible():
                continue
            duration_per_day = defaultdict(float)
            resource_intervals = resource_work_intervals.get(resource.id, Intervals())
            for interval_start, interval_end, _dummy in resource_intervals:
                # thanks to default periods structure, start and end should be in same day (with a same timezone !!)
                day = interval_start.date()
                # custom timeoff can divide a day to > 1 intervals
                duration_per_day[day] += (interval_end - interval_start).total_seconds() / 3600

            for day, hours in duration_per_day.items():
                day_working_hours = min(hours, resource.calendar_id.hours_per_day)
                # only days inside the original period
                if day >= start_day and day <= end_day:
                    resource_hours_per_day[resource.id][day] = day_working_hours

                year_week = weeknumber(babel_locale_parse(locale), day)
                year, week = year_week
                if (year < end_year) or (year == end_year and week <= end_week):
                    # cap weekly hours to the calendar's configured hours_per_week (not the
                    # company default full_time_required_hours which does not respect
                    # part-time schedules).
                    cap = resource.calendar_id.hours_per_week or resource.calendar_id.full_time_required_hours
                    resource_hours_per_week[resource.id][year_week] = min(cap, day_working_hours + resource_hours_per_week[resource.id][year_week])

        for calendar, resources in calendar_resources.items():
            domain = [('calendar_id', '=', False)] if not calendar else None
            leave_intervals = (calendar or self.env['resource.calendar'])._leave_intervals_batch(min_start_date, max_end_date, resources, domain)
            for resource_id, leaves in leave_intervals.items():
                if not resource_id:
                    continue

                ranges_to_remove = []
                for leave in leaves._items:
                    resource_by_id[resource_id]._format_leave(leave, resource_hours_per_day, resource_hours_per_week, ranges_to_remove, start_day, end_day, locale)

                resource_work_intervals[resource_id] -= Intervals(ranges_to_remove)

        for resource_id, work_intervals in resource_work_intervals.items():
            tz = timezone(resource_by_id[resource_id].tz or self.env.user.tz)
            resource_work_intervals[resource_id] = work_intervals & Intervals([(start.astimezone(tz), end.astimezone(tz), self.env['resource.calendar.attendance'])])

        return resource_work_intervals, resource_hours_per_day, resource_hours_per_week