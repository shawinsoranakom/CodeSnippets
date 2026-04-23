def action_create_users(self):
        def _get_user_creation_notification_action(message, message_type, next_action):
            return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': self.env._("User Creation Notification"),
                        'type': message_type,
                        'message': message,
                        'next': next_action
                    }
                }

        employee_emails = [
            normalized_email
            for employee in self
            for normalized_email in tools.mail.email_normalize_all(employee.work_email)
        ]
        conflicting_users = self.env['res.users']
        if employee_emails:
            conflicting_users = self.env['res.users'].search([
                '|', ('email_normalized', 'in', employee_emails),
                ('login', 'in', employee_emails),
            ])
        emp_by_email = self.grouped(lambda employee: email_normalize(employee.work_email))
        duplicate_emails = [email for email, employees in emp_by_email.items() if email and len(employees) > 1]
        old_users = []
        new_users = []
        users_without_emails = []
        users_with_invalid_emails = []
        users_with_existing_email = []
        employees_with_duplicate_email = []
        for employee in self:
            normalized_email = email_normalize(employee.work_email)
            if employee.user_id:
                old_users.append(employee.name)
                continue
            if not employee.work_email:
                users_without_emails.append(employee.name)
                continue
            if not normalized_email:
                users_with_invalid_emails.append(employee.name)
                continue
            if normalized_email in conflicting_users.mapped('email_normalized'):
                users_with_existing_email.append(employee.name)
                continue
            if normalized_email in duplicate_emails:
                employees_with_duplicate_email.append(employee.name)
                continue
            new_users.append({
                'create_employee_id': employee.id,
                'name': employee.name,
                'phone': employee.work_phone,
                'login': normalized_email,
                'partner_id': employee.work_contact_id.id,
            })

        next_action = {'type': 'ir.actions.act_window_close'}
        if new_users:
            self.env['res.users'].create(new_users)
            message = _('Users %s creation successful', ', '.join([user['name'] for user in new_users]))
            next_action = _get_user_creation_notification_action(message, 'success', {
                "type": "ir.actions.client",
                "tag": "soft_reload",
                "params": {"next": next_action},
            })

        if old_users:
            message = _('User already exists for Those Employees %s', ', '.join(old_users))
            next_action = _get_user_creation_notification_action(message, 'warning', next_action)

        if users_without_emails:
            message = _("You need to set the work email address for %s", ', '.join(users_without_emails))
            next_action = _get_user_creation_notification_action(message, 'danger', next_action)

        if users_with_invalid_emails:
            message = _("You need to set a valid work email address for %s", ', '.join(users_with_invalid_emails))
            next_action = _get_user_creation_notification_action(message, 'danger', next_action)

        if users_with_existing_email:
            message = _('User already exists with the same email for Employees %s', ', '.join(users_with_existing_email))
            next_action = _get_user_creation_notification_action(message, 'warning', next_action)

        if employees_with_duplicate_email:
            message = _('The following employees have the same work email address: %s', ', '.join(employees_with_duplicate_email))
            next_action = _get_user_creation_notification_action(message, 'warning', next_action)

        return next_action