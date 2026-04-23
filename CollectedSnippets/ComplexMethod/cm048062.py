def _compute_has_mandatory_day(self):
        date_from, date_to = min(self.mapped('date_from')), max(self.mapped('date_to'))
        if date_from and date_to:
            # Sudo to get access to version fields on employee (job_id)
            mandatory_days = self.employee_id.sudo()._get_mandatory_days(
                date_from.date(),
                date_to.date())

            for leave in self:
                department_ids = leave.employee_id.department_id.ids
                domain = [
                    ('start_date', '<=', leave.date_to.date()),
                    ('end_date', '>=', leave.date_from.date()),
                    '|',
                        ('resource_calendar_id', '=', False),
                        ('resource_calendar_id', '=', leave.resource_calendar_id.id),
                ]
                if department_ids:
                    domain += [
                        '|',
                        ('department_ids', '=', False),
                        ('department_ids', 'parent_of', department_ids),
                    ]
                else:
                    domain += [('department_ids', '=', False)]

                if leave.holiday_status_id.company_id:
                    domain += [('company_id', '=', leave.holiday_status_id.company_id.id)]
                leave.has_mandatory_day = leave.date_from and leave.date_to and mandatory_days.filtered_domain(domain)
        else:
            self.has_mandatory_day = False