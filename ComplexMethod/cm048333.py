def _get_rules_intervals_by_timing_type(self, min_check_in, max_check_out, employees, schedules_intervals_by_employee):

        def _generate_days_intervals(intervals):
            days_intervals = []
            dates = set()
            for interval in intervals:
                start_datetime = interval[0]
                if start_datetime.time() == datetime.max.time():
                    start_datetime += relativedelta(days=1)
                start_day = start_datetime.date()
                stop_datetime = interval[1]
                if stop_datetime.time() == datetime.min.time():
                    stop_datetime -= relativedelta(days=1)
                stop_day = stop_datetime.date()
                if stop_day < start_day:
                    continue
                start = datetime.combine(start_day, datetime.min.time())
                stop = datetime.combine(stop_day, datetime.max.time())
                for day in rrule(freq=DAILY, dtstart=start, until=stop):
                    dates.add(day.date())
            for date in dates:
                days_intervals.append(
                    (
                        datetime.combine(date, datetime.min.time()),
                        datetime.combine(date, datetime.max.time()),
                        self.env['resource.calendar']
                    )
                )
            return Intervals(days_intervals, keep_distinct=True)

        def _invert_intervals(intervals, first_start, last_stop):
            # Redefintion of the method to return an interval
            items = []
            prev_stop = first_start
            if not intervals:
                return Intervals([(first_start, last_stop, self.env['resource.calendar'])])
            for start, stop, record in sorted(intervals):
                if prev_stop and prev_stop < start and (float_compare((last_stop - start).total_seconds(), 0, precision_digits=1) >= 0):
                    items.append((prev_stop, start, record))
                prev_stop = max(prev_stop, stop)
            if last_stop and prev_stop < last_stop:
                items.append((prev_stop, last_stop, record))
            return Intervals(items, keep_distinct=True)

        timing_rule_by_timing_type = self.grouped('timing_type')
        timing_type_set = set(timing_rule_by_timing_type.keys())

        intervals_by_timing_type = {
            'leave': schedules_intervals_by_employee['leave'],
            'schedule': defaultdict(lambda: defaultdict(Intervals)),
            'work_days': defaultdict(),
            'non_work_days': defaultdict()
        }

        for employee in employees:
            if {'work_days', 'non_work_days'} & timing_type_set:
                intervals_by_timing_type['work_days'][employee] = _generate_days_intervals(
                    schedules_intervals_by_employee['schedule'][employee]['work'] - schedules_intervals_by_employee['leave'][employee]
                )
            if 'non_work_days' in timing_type_set:
                intervals_by_timing_type['non_work_days'][employee] = _generate_days_intervals(
                    _invert_intervals(
                        intervals_by_timing_type['work_days'][employee],
                        datetime.combine(min_check_in, datetime.min.time()),
                        datetime.combine(max_check_out, datetime.max.time())
                    )
                )
        if 'schedule' in timing_type_set:
            for calendar in timing_rule_by_timing_type['schedule'].resource_calendar_id:
                start_datetime = utc.localize(datetime.combine(min_check_in, datetime.min.time())) - relativedelta(days=1)  # to avoid timezone shift
                stop_datetime = utc.localize(datetime.combine(max_check_out, datetime.max.time())) + relativedelta(days=1)  # to avoid timezone shift
                interval = calendar._attendance_intervals_batch(start_datetime, stop_datetime, lunch=True)[False]
                interval |= calendar._attendance_intervals_batch(start_datetime, stop_datetime)[False]
                naive_interval = Intervals([(
                    i_start.replace(tzinfo=None),
                    i_stop.replace(tzinfo=None),
                    i_model
                ) for i_start, i_stop, i_model in interval._items])
                calendar_intervals = _invert_intervals(
                    naive_interval,
                    start_datetime.replace(tzinfo=None),
                    stop_datetime.replace(tzinfo=None)
                )
                intervals_by_timing_type['schedule'][calendar.id].update(
                    {employee: calendar_intervals for employee in employees}
                )
        return intervals_by_timing_type