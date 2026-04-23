def write(self, vals):
        if 'advanced_employee_ids' not in vals:
            vals['advanced_employee_ids'] = []
        group_users = self.sudo()._get_group_pos_manager().with_company(self.company_id).user_ids.filtered(
            lambda u: self.company_id in u.company_ids
        )
        allowed_employees = group_users.sudo().mapped('employee_id')
        if not allowed_employees and group_users:
            target_user = group_users.sudo().with_company(self.company_id).filtered(lambda user: not user.employee_id)[0]
            target_user.action_create_employee()
            allowed_employees = target_user.employee_id

        # Update the vals list
        vals['advanced_employee_ids'] += [(4, emp.id) for emp in allowed_employees]

        # write employees in sudo, because we have no access to these corecords
        sudo_vals = {
            field_name: vals.pop(field_name)
            for field_name in ('minimal_employee_ids', 'basic_employee_ids', 'advanced_employee_ids')
            if not self.env.su
            if isinstance(vals.get(field_name), list)
            if all(isinstance(cmd, (list, tuple)) for cmd in vals[field_name])
        }

        res = super().write(vals)
        if sudo_vals:
            super(PosConfig, self.sudo()).write(sudo_vals)
        return res