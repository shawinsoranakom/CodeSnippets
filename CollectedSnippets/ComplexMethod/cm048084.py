def write(self, vals):
        values = vals
        # Prevent the resource calendar of leaves to be updated by a write to
        # employee. When this module is enabled the resource calendar of
        # leaves are determined by those of the contracts.
        self = self.with_context(no_leave_resource_calendar_update=True)  # noqa: PLW0642
        if 'parent_id' in values:
            manager = self.env['hr.employee'].browse(values['parent_id']).user_id
            if manager:
                to_change = self.filtered(lambda e: e.leave_manager_id == e.parent_id.user_id or not e.leave_manager_id)
                to_change.write({'leave_manager_id': values.get('leave_manager_id', manager.id)})

        old_managers = self.env['res.users']
        if 'leave_manager_id' in values:
            old_managers = self.mapped('leave_manager_id')
            if values['leave_manager_id']:
                leave_manager = self.env['res.users'].browse(values['leave_manager_id'])
                old_managers -= leave_manager
                approver_group = self.env.ref('hr_holidays.group_hr_holidays_responsible', raise_if_not_found=False)
                if approver_group and not leave_manager.has_group('hr_holidays.group_hr_holidays_responsible'):
                    leave_manager.sudo().write({'group_ids': [(4, approver_group.id)]})

        res = super().write(values)
        # remove users from the Responsible group if they are no longer leave managers
        old_managers.sudo()._clean_leave_responsible_users()

        # Change the resource calendar of the employee's leaves in the future
        # Other modules can disable this behavior by setting the context key
        # 'no_leave_resource_calendar_update'
        if 'resource_calendar_id' in values and not self.env.context.get('no_leave_resource_calendar_update'):
            try:
                leaves = self.env['hr.leave'].search([
                    ('employee_id', 'in', self.ids),
                    ('resource_calendar_id', '!=', int(values['resource_calendar_id'])),
                    ('date_from', '>', fields.Datetime.now())])
                leaves.write({'resource_calendar_id': values['resource_calendar_id']})
                non_hourly_leaves = leaves.filtered(lambda l: not l.request_unit_hours)
                non_hourly_leaves.with_context(leave_skip_date_check=True, leave_skip_state_check=True)._compute_date_from_to()
                non_hourly_leaves.filtered(lambda l: l.state == 'validate')._validate_leave_request()
            except ValidationError:
                raise ValidationError(_("Changing this working schedule results in the affected employee(s) not having enough "
                                        "leaves allocated to accomodate for their leaves already taken in the future. Please "
                                        "review this employee's leaves and adjust their allocation accordingly."))

        if 'parent_id' in values or 'department_id' in values:
            today_date = fields.Datetime.now()
            hr_vals = {}
            if values.get('department_id') is not None:
                hr_vals['department_id'] = values['department_id']
            holidays = self.env['hr.leave'].sudo().search([
                '|',
                ('state', '=', 'confirm'),
                ('date_from', '>', today_date),
                ('employee_id', 'in', self.ids),
            ])
            holidays.write(hr_vals)
            if values.get('parent_id') is not None:
                hr_vals['manager_id'] = values['parent_id']
            allocations = self.env['hr.leave.allocation'].sudo().search([
                ('state', '=', 'confirm'),
                ('employee_id', 'in', self.ids),
            ])
            allocations.write(hr_vals)
        return res