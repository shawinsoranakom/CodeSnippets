def _check_presence(self):
        company = self.env.company
        employees = self.env['hr.employee'].search([('company_id', '=', company.id)])

        employees.write({
            'email_sent': False,
            'ip_connected': False,
            'manually_set_present': False,
            'manually_set_presence': False,
        })

        all_employees = employees


        # Check on IP
        if company.hr_presence_control_ip:
            ip_list = company.hr_presence_control_ip_list
            ip_list = ip_list.split(',') if ip_list else []
            ip_employees = self.env['hr.employee']
            for employee in employees:
                employee_ips = self.env['res.users.log'].sudo().search([
                    ('create_uid', '=', employee.user_id.id),
                    ('ip', '!=', False),
                    ('create_date', '>=', Datetime.to_string(Datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)))]
                ).mapped('ip')
                if any(ip in ip_list for ip in employee_ips):
                    ip_employees |= employee
            ip_employees.write({'ip_connected': True})
            employees = employees - ip_employees

        # Check on sent emails
        if company.hr_presence_control_email:
            email_employees = self.env['hr.employee']
            threshold = company.hr_presence_control_email_amount
            for employee in employees:
                sent_emails = self.env['mail.message'].search_count([
                    ('author_id', '=', employee.user_id.partner_id.id),
                    ('date', '>=', Datetime.to_string(Datetime.now().replace(hour=0, minute=0, second=0, microsecond=0))),
                    ('date', '<=', Datetime.to_string(Datetime.now()))])
                if sent_emails >= threshold:
                    email_employees |= employee
            email_employees.write({'email_sent': True})
            employees = employees - email_employees

        company.sudo().hr_presence_last_compute_date = Datetime.now()

        for employee in all_employees:
            employee.hr_presence_state_display = employee.hr_presence_state