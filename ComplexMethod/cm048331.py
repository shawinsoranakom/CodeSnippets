def _get1_timing_overtime_intervals(self, attendances, version_map):
        self.ensure_one()
        attendances.employee_id.ensure_one()
        assert self.base_off == 'timing'

        employee = attendances.employee_id
        start_dt = min(attendances.mapped('check_in'))
        end_dt = max(attendances.mapped('check_out'))

        if self.timing_type in ['work_days', 'non_work_days']:
            company = self.company_id or employee.company_id
            unusual_days = company.resource_calendar_id._get_unusual_days(start_dt, end_dt, company_id=company)

            attendance_intervals = []
            for date, day_attendances in attendances.filtered(
                lambda att: unusual_days.get(att.date.strftime('%Y-%m-%d'), None) == (self.timing_type == 'non_work_days')
            ).grouped('date').items():
                tz = timezone(version_map[employee][date]._get_tz())
                time_start = self._get_local_time_start(date, tz)
                time_stop = self._get_local_time_stop(date, tz)

                attendance_intervals.extend([(
                        max(time_start, attendance.check_in),
                        min(time_stop, attendance.check_out),
                        attendance,
                    ) for attendance in day_attendances
                    if time_start <= attendance.check_out and attendance.check_in <= time_stop
                ])

            overtime_intervals = Intervals(attendance_intervals, keep_distinct=True)
        else:
            attendance_intervals = [
                (att.check_in, att.check_out, att)
                for att in attendances
            ]
            resource = attendances.employee_id.resource_id
            # Just use last version for now
            last_version = version_map[employee][max(attendances.mapped('date'))]
            tz = timezone(last_version._get_tz())
            if self.timing_type == 'schedule':
                work_schedule = self.resource_calendar_id
                work_intervals = Intervals()
                for lunch in [False, True]:
                    work_intervals |= Intervals(
                        (_naive_utc(start), _naive_utc(end), records)
                        for (start, end, records)
                        in work_schedule._attendance_intervals_batch(
                            utc.localize(start_dt),
                            utc.localize(end_dt),
                            resource,
                            tz=tz,
                            lunch=lunch,
                        )[resource.id]
                    )
                overtime_intervals = Intervals(attendance_intervals, keep_distinct=True) - work_intervals
            elif self.timing_type == 'leave':
                # TODO: completely untested
                leave_intervals = last_version.resource_calendar_id._leave_intervals_batch(
                    utc.localize(start_dt),
                    utc.localize(end_dt),
                    resource,
                    tz=tz,
                )[resource.id]
                overtime_intervals = Intervals(attendance_intervals, keep_distinct=True) & leave_intervals

        if self.employer_tolerance:
            overtime_intervals = Intervals((
                    ot for ot in overtime_intervals
                    if _time_delta_hours(ot[1] - ot[0]) >= self.employer_tolerance
                ),
                keep_distinct=True,
            )
        return overtime_intervals