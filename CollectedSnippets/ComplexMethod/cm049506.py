def _get_attendance_intervals(self, start_dt, end_dt):
        assert start_dt.tzinfo and end_dt.tzinfo, "function expects localized date"
        # {resource: intervals}
        employees_by_calendar = defaultdict(lambda: self.env['hr.employee'])
        for version in self:
            if version.work_entry_source != 'calendar':
                continue
            employees_by_calendar[version.resource_calendar_id] |= version.employee_id
        result = dict()
        for calendar, employees in employees_by_calendar.items():
            if not calendar:
                for employee in employees:
                    result.update({employee.resource_id.id: Intervals([(start_dt, end_dt, self.env['resource.calendar.attendance'])])})
            else:
                result.update(calendar._attendance_intervals_batch(
                    start_dt,
                    end_dt,
                    resources=employees.resource_id,
                    tz=pytz.timezone(calendar.tz) if calendar.tz else pytz.utc
                ))
        return result