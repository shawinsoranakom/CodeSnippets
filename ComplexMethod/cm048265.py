def _generate_timesheets(self, ignored_resource_calendar_leaves=None):
        """ Timesheet will be generated on leave validation
            internal_project_id and leave_timesheet_task_id are used.
            The generated timesheet will be attached to this project/task.
        """
        vals_list = []
        leave_ids = []
        calendar_leaves_data = self.env['resource.calendar.leaves']._read_group([('holiday_id', 'in', self.ids)], ['holiday_id'], ['id:array_agg'])
        mapped_calendar_leaves = {leave: calendar_leave_ids[0] for leave, calendar_leave_ids in calendar_leaves_data}
        for leave in self:
            project, task = leave.employee_id.company_id.internal_project_id, leave.employee_id.company_id.leave_timesheet_task_id

            if not project or not task or leave.holiday_status_id.time_type == 'other':
                continue

            leave_ids.append(leave.id)
            if not leave.employee_id:
                continue

            calendar = leave.resource_calendar_id
            calendar_timezone = pytz.timezone((calendar or leave.employee_id).tz)

            if calendar.flexible_hours and leave.date_from.date() == leave.date_to.date():
                leave_date = leave.date_from.astimezone(calendar_timezone).date()
                if leave.request_unit_hours:
                    hours = leave.request_hour_to - leave.request_hour_from
                elif leave.request_unit_half and leave.request_date_from_period == leave.request_date_to_period:
                    hours = calendar.hours_per_day / 2
                else:  # Single-day leave
                    hours = calendar.hours_per_day
                work_hours_data = [(leave_date, hours)]
            else:
                ignored_resource_calendar_leaves = ignored_resource_calendar_leaves or []
                if leave in mapped_calendar_leaves:
                    ignored_resource_calendar_leaves.append(mapped_calendar_leaves[leave])
                work_hours_data = leave.employee_id._list_work_time_per_day(
                    leave.date_from,
                    leave.date_to,
                    domain=[('id', 'not in', ignored_resource_calendar_leaves)] if ignored_resource_calendar_leaves else None,
                    calendar=calendar,
                )[leave.employee_id.id]

            for index, (day_date, work_hours_count) in enumerate(work_hours_data):
                vals_list.append(leave._timesheet_prepare_line_values(index, work_hours_data, day_date, work_hours_count, project, task))

        # Unlink previous timesheets to avoid doublon (shouldn't happen on the interface but meh). Necessary when the function is called to regenerate timesheets.
        old_timesheets = self.env["account.analytic.line"].sudo().search([('project_id', '!=', False), ('holiday_id', 'in', leave_ids)])
        if old_timesheets:
            old_timesheets.holiday_id = False
            old_timesheets.unlink()

        self.env['account.analytic.line'].sudo().create(vals_list)