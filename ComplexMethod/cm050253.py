def action_register_departure(self):
        def _get_user_archive_notification_action(message, message_type, next_action):
            return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': self.env._("User Archive Notification"),
                        'type': message_type,
                        'message': message,
                        'next': next_action,
                    },
                }

        employee_ids = self.employee_ids
        active_versions = employee_ids.version_id

        if any(v.contract_date_start and v.contract_date_start > self.departure_date for v in active_versions):
            raise UserError(self.env._("Departure date can't be earlier than the start date of current contract."))

        allow_archived_users = self.env['res.users']
        unarchived_users = self.env['res.users']
        if self.remove_related_user:
            related_users = employee_ids.grouped('user_id')
            related_employees_count = dict(self.env['hr.employee'].sudo()._read_group(
                    domain=[('user_id', 'in', employee_ids.user_id.ids)],
                    groupby=['user_id'],
                    aggregates=['id:count'],
                ))
            for user, emps in related_users.items():
                if not user:
                    continue
                if len(emps) == related_employees_count.get(user, 0):
                    allow_archived_users |= user
                else:
                    unarchived_users |= user

        archived_employees = self.env['hr.employee']
        archived_users = self.env['res.users']
        for employee in employee_ids.filtered(lambda emp: emp.active):
            if self.env.context.get('employee_termination', False):
                archived_employees |= employee
                if self.remove_related_user and employee.user_id in allow_archived_users:
                    archived_users |= employee.user_id

        archived_employees.with_context(no_wizard=True).action_archive()
        archived_users.action_archive()

        employee_ids.write({
            'departure_reason_id': self.departure_reason_id,
            'departure_description': self.departure_description,
            'departure_date': self.departure_date,
        })

        if self.set_date_end:
            # Write date and update state of current contracts
            active_versions = active_versions.filtered(lambda v: v.contract_date_start)
            active_versions.write({'contract_date_end': self.departure_date})

        next_action = {'type': 'ir.actions.act_window_close'}
        if archived_users:
            message = self.env._(
                "The following users have been archived: %s",
                ', '.join(archived_users.mapped('name'))
            )
            next_action = _get_user_archive_notification_action(message, 'success', next_action)
        if unarchived_users:
            message = self.env._(
                "The following users have not been archived as they are still linked to another active employees: %s",
                ', '.join(unarchived_users.mapped('name'))
            )
            next_action = _get_user_archive_notification_action(message, 'danger', next_action)

        return next_action