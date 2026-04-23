def _get_daterange_overtime_undertime_intervals_for_quantity_rule(self, start, stop, attendance_intervals, schedule):
        self.ensure_one()
        expected_duration = self.expected_hours
        attendances_interval_without_lunch = []
        intervals_attendance_by_attendance = defaultdict(Intervals)
        attendances = self.env['hr.attendance']
        for (a_start, a_stop, attendance) in attendance_intervals:
            attendances += attendance
            intervals_attendance_by_attendance[attendance] = (Intervals([(a_start, a_stop, self.env['resource.calendar'])]) - (schedule['lunch'] - schedule['leave'])) &\
                Intervals([(start, stop, self.env['resource.calendar'])])
            attendances_interval_without_lunch.extend(intervals_attendance_by_attendance[attendance]._items)

        if self.expected_hours_from_contract:
            period_schedule = (schedule['work'] - schedule['leave']) & Intervals([(start, stop, self.env['resource.calendar'])])
            expected_duration = sum_intervals(period_schedule)

        overtime_amount = sum_intervals(Intervals(attendances_interval_without_lunch)) - expected_duration
        employee = attendances.employee_id
        company = self.company_id or employee.company_id
        if company.absence_management and float_compare(overtime_amount, -self.employee_tolerance, 5) == -1:
            if not intervals_attendance_by_attendance:
                return {}, {}
            last_attendance = sorted(intervals_attendance_by_attendance.keys(), key=lambda att: att.check_out)[-1]
            return {}, {last_attendance: [(overtime_amount, self)]}

        if float_compare(overtime_amount, self.employer_tolerance, 5) != 1:
            return {}, {}

        overtime_intervals = defaultdict(list)
        remaining_duration = expected_duration
        remanining_overtime_amount = overtime_amount
        # Attendances are sorted by check_in asc
        for attendance in attendances.sorted('check_in'):
            for start, stop, _cal in intervals_attendance_by_attendance[attendance]:
                interval_duration = (stop - start).total_seconds() / 3600
                if remaining_duration >= interval_duration:
                    remaining_duration -= interval_duration
                    continue
                interval_overtime_duration = interval_duration
                if remaining_duration != 0:
                    interval_overtime_duration = interval_duration - remaining_duration
                new_start = stop - timedelta(hours=interval_overtime_duration)
                remaining_duration = 0
                overtime_intervals[attendance].append((new_start, stop, self))
                remanining_overtime_amount = remanining_overtime_amount - interval_overtime_duration
                if remanining_overtime_amount <= 0:
                    return overtime_intervals, {}
        return overtime_intervals, {}