def _unlink_except_active_pos_session(self):
        configs_with_employees = self.env['pos.config'].sudo().search([('module_pos_hr', '=', True)]).filtered(lambda c: c.current_session_id)
        configs_with_all_employees = configs_with_employees.filtered(lambda c: not c.basic_employee_ids and not c.advanced_employee_ids and not c.minimal_employee_ids)
        configs_with_specific_employees = configs_with_employees.filtered(lambda c: (c.basic_employee_ids or c.advanced_employee_ids or c.minimal_employee_ids) & self)
        if configs_with_all_employees or configs_with_specific_employees:
            error_msg = _("You cannot delete an employee that may be used in an active PoS session, close the session(s) first: \n")
            for employee in self:
                config_ids = configs_with_all_employees | configs_with_specific_employees.filtered(lambda c: employee in c.basic_employee_ids)
                if config_ids:
                    error_msg += _("Employee: %(employee)s - PoS Config(s): %(config_list)s \n", employee=employee.name, config_list=config_ids.mapped("name"))

            raise UserError(error_msg)