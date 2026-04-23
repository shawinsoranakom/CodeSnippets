def _timesheet_create_lines(self):
        """ Create timesheet leaves for each employee using the same calendar containing in self.calendar_id

            If the employee has already a time off in the same day then no timesheet should be created.
        """
        resource_calendars = self._get_resource_calendars()
        work_hours_data = self._work_time_per_day(resource_calendars)
        employees_groups = self.env['hr.employee']._read_group(
            [('resource_calendar_id', 'in', resource_calendars.ids), ('company_id', 'in', self.company_id.ids if self.company_id else self.env.companies.ids)],
            ['resource_calendar_id'],
            ['id:recordset'])
        mapped_employee = {
            resource_calendar.id: employees
            for resource_calendar, employees in employees_groups
        }
        employee_ids_all = [_id for __, employees in employees_groups for _id in employees._ids]
        min_date = max_date = None
        for values in work_hours_data.values():
            for vals in values.values():
                for d, _dummy in vals:
                    if not min_date and not max_date:
                        min_date = max_date = d
                    elif d < min_date:
                        min_date = d
                    elif d > max_date:
                        max_date = d

        holidays_read_group = self.env['hr.leave']._read_group([
            ('employee_id', 'in', employee_ids_all),
            ('date_from', '<=', max_date),
            ('date_to', '>=', min_date),
            ('state', '=', 'validate'),
        ], ['employee_id'], ['date_from:array_agg', 'date_to:array_agg'])
        holidays_by_employee = {
            employee.id: [
                (date_from.date(), date_to.date()) for date_from, date_to in zip(date_from_list, date_to_list)
            ] for employee, date_from_list, date_to_list in holidays_read_group
        }
        vals_list = []

        def get_timesheets_data(employees, work_hours_list, vals_list):
            for employee in employees:
                holidays = holidays_by_employee.get(employee.id)
                for index, (day_date, work_hours_count) in enumerate(work_hours_list):
                    if not holidays or all(not (date_from <= day_date and date_to >= day_date) for date_from, date_to in holidays):
                        vals_list.append(
                            leave._timesheet_prepare_line_values(
                                index,
                                employee,
                                work_hours_list,
                                day_date,
                                work_hours_count
                            )
                        )
            return vals_list

        for leave in self:
            if not leave.calendar_id:
                for calendar_id, calendar_employees in mapped_employee.items():
                    work_hours_list = work_hours_data[calendar_id][leave.id]
                    vals_list = get_timesheets_data(calendar_employees, work_hours_list, vals_list)
            else:
                employees = mapped_employee.get(leave.calendar_id.id, self.env['hr.employee'])
                work_hours_list = work_hours_data[leave.calendar_id.id][leave.id]
                vals_list = get_timesheets_data(employees, work_hours_list, vals_list)

        return self.env['account.analytic.line'].sudo().create(vals_list)