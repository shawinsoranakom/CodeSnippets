def _generate_public_time_off_timesheets(self, employees):
        timesheet_vals_list = []
        resource_calendars = self._get_resource_calendars()
        work_hours_data = self._work_time_per_day(resource_calendars)
        timesheet_read_group = self.env['account.analytic.line']._read_group(
            [('global_leave_id', 'in', self.ids), ('employee_id', 'in', employees.ids)],
            ['employee_id'],
            ['date:array_agg']
        )
        timesheet_dates_per_employee_id = {
            employee.id: date
            for employee, date in timesheet_read_group
        }
        for leave in self:
            for employee in employees:
                if leave.calendar_id and employee.resource_calendar_id != leave.calendar_id:
                    continue
                calendar = leave.calendar_id or employee.resource_calendar_id
                work_hours_list = work_hours_data[calendar.id][leave.id]
                timesheet_dates = timesheet_dates_per_employee_id.get(employee.id, [])
                for index, (day_date, work_hours_count) in enumerate(work_hours_list):
                    generate_timesheet = day_date not in timesheet_dates
                    if not generate_timesheet:
                        continue
                    timesheet_vals = leave._timesheet_prepare_line_values(
                        index,
                        employee,
                        work_hours_list,
                        day_date,
                        work_hours_count
                    )
                    timesheet_vals_list.append(timesheet_vals)
        return self.env['account.analytic.line'].sudo().create(timesheet_vals_list)