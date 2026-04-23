def _get_all_overtime_intervals_for_timing_rule(self, min_check_in, max_check_out, attendances, schedules_intervals_by_employee):

        def _fill_overtime(employees, rules, intervals, attendances_intervals):
            if not intervals:
                return
            for employee in employees:
                intersetion_interval_for_attendance = attendances_intervals[employee] & intervals[employee]
                overtime_interval_list = defaultdict(list)
                for (start, stop, attendance) in intersetion_interval_for_attendance:
                    overtime_interval_list[attendance].append((start, stop, rules))
                for attendance, attendance_intervals_list in overtime_interval_list.items():
                    overtime_by_employee_by_attendance[employee][attendance] |= Intervals(attendance_intervals_list)

        def _build_day_rule_intervals(employees, rule, intervals):
            timing_intervals_by_employee = defaultdict(Intervals)
            start = min(rule.timing_start, rule.timing_stop)
            stop = max(rule.timing_start, rule.timing_stop)
            for employee in employees:
                for interval in intervals[employee]:
                    start_datetime = datetime.combine(interval[0].date(), float_to_time(start))
                    stop_datetime = datetime.combine(interval[0].date(), float_to_time(stop))
                    timing_intervals = Intervals([(start_datetime, stop_datetime, self.env['resource.calendar'])])
                    if rule.timing_start > rule.timing_stop:
                        day_start = datetime.combine(interval[0].date(), datetime.min.time())
                        day_end = datetime.combine(interval[0].date(), datetime.max.time())
                        timing_intervals = Intervals([
                            (i_start, i_stop, self.env['resource.calendar'])
                        for i_start, i_stop in invert_intervals([(start_datetime, stop_datetime)], day_start, day_end)])
                    timing_intervals_by_employee[employee] |= timing_intervals
            return timing_intervals_by_employee

        employees = attendances.employee_id
        intervals_by_timing_type = self._get_rules_intervals_by_timing_type(
            min_check_in,
            max_check_out,
            employees,
            schedules_intervals_by_employee
        )
        attendances_intervals_by_employee = defaultdict()
        overtime_by_employee_by_attendance = defaultdict(lambda: defaultdict(Intervals))

        attendances_by_employee = attendances.grouped('employee_id')
        for employee, emp_attendance in attendances_by_employee.items():
            attendances_intervals_by_employee[employee] = Intervals([
                (*(attendance._get_localized_times()), attendance)
            for attendance in emp_attendance], keep_distinct=True)

        for timing_type, rules in self.grouped('timing_type').items():
            if timing_type == 'leave':
                _fill_overtime(employees, rules, intervals_by_timing_type['leave'], attendances_intervals_by_employee)

            elif timing_type == 'schedule':
                for calendar, rules in rules.grouped('resource_calendar_id').items():
                    outside_calendar_intervals = intervals_by_timing_type['schedule'][calendar.id]
                    _fill_overtime(employees, rules, outside_calendar_intervals, attendances_intervals_by_employee)
            else:
                for rule in rules:
                    timing_intervals_by_employee = _build_day_rule_intervals(employees, rule, intervals_by_timing_type[timing_type])
                    _fill_overtime(employees, rule, timing_intervals_by_employee, attendances_intervals_by_employee)
        return overtime_by_employee_by_attendance