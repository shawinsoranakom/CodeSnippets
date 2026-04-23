def write(self, vals):
        """
        Synchronize user and its related employee
        and check access rights if employees are not allowed to update
        their own data (otherwise sudo is applied for self data).
        """
        hr_fields = {
            field_name: field
            for field_name, field in self._fields.items()
            if field.related_field and field.related_field.model_name == 'hr.employee' and field_name in vals
        }

        employee_domain = [
            *self.env['hr.employee']._check_company_domain(self.env.company),
            ('user_id', 'in', self.ids),
        ]
        if hr_fields:
            employees = self.env['hr.employee'].sudo().search(employee_domain)
            get_field = self.env['ir.model.fields']._get
            field_names = Markup().join([
                 Markup("<li>%s</li>") % get_field("res.users", fname).field_description for fname in hr_fields
            ])
            for employee in employees:
                reason_message, partner_ids = self._get_personal_info_partner_ids_to_notify(employee)
                if partner_ids:
                    employee.message_notify(
                        body=Markup("<p>%s</p><p>%s</p><ul>%s</ul><p><em>%s</em></p>") % (
                            _('Personal information update.'),
                            _("The following fields were modified by %s", employee.name),
                            field_names,
                            reason_message,
                        ),
                        partner_ids=partner_ids,
                    )
        result = super().write(vals)

        employee_values = {}
        for fname in [f for f in self._get_employee_fields_to_sync() if f in vals]:
            employee_values[fname] = vals[fname]

        if employee_values:
            if 'email' in employee_values:
                employee_values['work_email'] = employee_values.pop('email')
            if 'image_1920' in vals:
                without_image = self.env['hr.employee'].sudo().search(employee_domain + [('image_1920', '=', False)])
                with_image = self.env['hr.employee'].sudo().search(employee_domain + [('image_1920', '!=', False)])
                without_image.write(employee_values)
                with_image.write(employee_values)
            else:
                employees = self.env['hr.employee'].sudo().search(employee_domain)
                if employees:
                    employees.write(employee_values)
        return result