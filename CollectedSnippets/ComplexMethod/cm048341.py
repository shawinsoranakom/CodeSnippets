def _get_schedules_by_employee_by_work_type(self, start, stop, version_periods_by_employee):
        employees_by_calendar = defaultdict(lambda: self.env['hr.employee'])
        leave_intervals_by_cal_by_resource = defaultdict(lambda: defaultdict(Intervals))
        attendance_intervals_by_cal = defaultdict(Intervals)
        lunch_intervals_by_cal = defaultdict(Intervals)

        for employee, intervals in version_periods_by_employee.items():
            for (_start, _stop, version) in intervals:
                employees_by_calendar[version.resource_calendar_id] |= employee

        for cal, employees in employees_by_calendar.items():
            if not cal:  # employees are fully flex
                continue
            cal_leave_intervals_by_resource = cal._leave_intervals_batch(
                start,
                stop,
                resources=employees.resource_id,
            )
            for resource, leave_intervals in cal_leave_intervals_by_resource.items():
                naive_leave_intervals = Intervals([(
                    i_start.replace(tzinfo=None),
                    i_stop.replace(tzinfo=None),
                    i_model
                ) for (i_start, i_stop, i_model) in leave_intervals])
                leave_intervals_by_cal_by_resource[cal][resource] = naive_leave_intervals

            cal_attendance_intervals = cal._attendance_intervals_batch(
                start,
                stop,
            )[False]
            attendance_intervals_by_cal[cal] = Intervals([(
                    i_start.replace(tzinfo=None),
                    i_stop.replace(tzinfo=None),
                    i_model
                ) for (i_start, i_stop, i_model) in cal_attendance_intervals])

            cal_lunch_intervals = cal._attendance_intervals_batch(
                start,
                stop,
                lunch=True
            )[False]
            lunch_intervals_by_cal[cal] = Intervals([(
                    i_start.replace(tzinfo=None),
                    i_stop.replace(tzinfo=None),
                    i_model
                ) for (i_start, i_stop, i_model) in cal_lunch_intervals])

        full_schedule_by_employee = {
            'leave': defaultdict(Intervals),
            'schedule': defaultdict(lambda: {
                'work': Intervals([]),
                'lunch': Intervals([]),
            }),
            'fully_flexible': defaultdict(Intervals)
        }
        for employee, intervals in version_periods_by_employee.items():
            for (p_start, p_stop, version) in intervals:
                interval = Intervals([(p_start.replace(tzinfo=None), p_stop.replace(tzinfo=None), self.env['resource.calendar'])])
                calendar = version.resource_calendar_id
                if not calendar:
                    full_schedule_by_employee['fully_flexible'][employee] |= interval
                    continue
                employee_leaves = leave_intervals_by_cal_by_resource[calendar][employee.resource_id.id]
                full_schedule_by_employee['leave'][employee] |= employee_leaves & interval
                employee_attendances = attendance_intervals_by_cal[calendar]
                full_schedule_by_employee['schedule'][employee]['work'] |= employee_attendances & interval
                employee_lunches = lunch_intervals_by_cal[calendar]
                full_schedule_by_employee['schedule'][employee]['lunch'] |= employee_lunches & interval

        return full_schedule_by_employee