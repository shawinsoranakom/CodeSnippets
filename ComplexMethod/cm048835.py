def _update_create_write_vals(self, vals):
        if 'driver_employee_id' in vals:
            partner = False
            if vals['driver_employee_id']:
                employee = self.env['hr.employee'].sudo().browse(vals['driver_employee_id'])
                partner = employee.work_contact_id.id
            vals['driver_id'] = partner
        elif 'driver_id' in vals:
            # Reverse the process if we can find a single employee
            employee = False
            if vals['driver_id']:
                # Limit to 2, we only care about the first one if he is the only one
                employee_ids = self.env['hr.employee'].sudo().search([
                    ('work_contact_id', '=', vals['driver_id'])
                ], limit=2)
                if len(employee_ids) == 1:
                    employee = employee_ids[0].id
            vals['driver_employee_id'] = employee

        # Same for future driver
        if 'future_driver_employee_id' in vals:
            partner = False
            if vals['future_driver_employee_id']:
                employee = self.env['hr.employee'].sudo().browse(vals['future_driver_employee_id'])
                partner = employee.work_contact_id.id
            vals['future_driver_id'] = partner
        elif 'future_driver_id' in vals:
            # Reverse the process if we can find a single employee
            employee = False
            if vals['future_driver_id']:
                # Limit to 2, we only care about the first one if he is the only one
                employee_ids = self.env['hr.employee'].sudo().search([
                    ('work_contact_id', '=', vals['future_driver_id'])
                ], limit=2)
                if len(employee_ids) == 1:
                    employee = employee_ids[0].id
            vals['future_driver_employee_id'] = employee