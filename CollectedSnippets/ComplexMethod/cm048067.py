def write(self, vals):
        values = vals
        is_officer = self.env.user.has_group('hr_holidays.group_hr_holidays_user') or self.env.is_superuser()
        if not is_officer and values.keys() - {'attachment_ids', 'supported_attachment_ids', 'message_main_attachment_id'}:
            if any(hol.date_from.date() < fields.Date.today() and hol.employee_id.leave_manager_id != self.env.user
                   and hol.state not in ('confirm', 'draft') for hol in self):
                raise UserError(_('You must have manager rights to modify/validate a time off that already begun'))
            if any(leave.state == 'cancel' for leave in self):
                raise UserError(_('Only a manager can modify a canceled leave.'))

        # If a leave changes state from validated or if the dates of a validated leave change
        # unlink the corresponding resource calendar leave
        date_fields = {'date_from', 'date_to', 'request_date_from', 'request_date_to'}
        validated_leaves = self.filtered(lambda l: l.state == 'validate')
        if validated_leaves and (('state' in values and values['state'] != 'validate') or date_fields.intersection(values)):
            validated_leaves._remove_resource_leave()

        employee_id = values.get('employee_id', False)
        if not self.env.context.get('leave_fast_create'):
            if values.get('state'):
                self._check_approval_update(values['state'])
                if any(holiday.validation_type == 'both' for holiday in self):
                    if values.get('employee_id'):
                        employees = self.env['hr.employee'].browse(values.get('employee_id'))
                    else:
                        employees = self.mapped('employee_id')
                    self._check_double_validation_rules(employees, values['state'])
            if 'date_from' in values:
                values['request_date_from'] = values['date_from']
            if 'date_to' in values:
                values['request_date_to'] = values['date_to']
        result = super().write(values)
        if any(field in values for field in ['request_date_from', 'date_from', 'request_date_from', 'date_to', 'holiday_status_id', 'employee_id', 'state']):
            if not values.get('state') or values.get('state') not in ('refuse', 'cancel'):
                self._check_validity()
            self.env['hr.leave.allocation'].invalidate_model(['leaves_taken', 'max_leaves'])  # missing dependency on compute
        if not self.env.context.get('leave_fast_create'):
            for holiday in self:
                if employee_id:
                    holiday.add_follower(employee_id)

        return result