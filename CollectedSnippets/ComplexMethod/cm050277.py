def action_archive(self):
        archived_employees = self.filtered('active')
        res = super().action_archive()
        if archived_employees:
            # Empty links to this employees (example: manager, coach, time off responsible, ...)
            employee_fields_to_empty = self._get_employee_m2o_to_empty_on_archived_employees()
            user_fields_to_empty = self._get_user_m2o_to_empty_on_archived_employees()
            employee_domain = Domain.OR(Domain(field, 'in', archived_employees.ids) for field in employee_fields_to_empty)
            user_domain = Domain.OR(Domain(field, 'in', archived_employees.user_id.ids) for field in user_fields_to_empty)
            employees = self.env['hr.employee'].search(employee_domain | user_domain)
            for employee in employees:
                for field in employee_fields_to_empty:
                    if employee[field] in archived_employees:
                        employee[field] = False
                for field in user_fields_to_empty:
                    if employee[field] in archived_employees.user_id:
                        employee[field] = False

            if len(archived_employees) == 1 and not self.env.context.get('no_wizard', False):
                return {
                    'type': 'ir.actions.act_window',
                    'name': _('Register Departure'),
                    'res_model': 'hr.departure.wizard',
                    'view_mode': 'form',
                    'target': 'new',
                    'context': {'active_id': self.id},
                    'views': [[False, 'form']]
                }
        return res