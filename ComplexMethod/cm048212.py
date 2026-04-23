def _compute_can_reset(self):
        user = self.env.user
        is_team_approver = user.has_group('hr_expense.group_hr_expense_team_approver') or self.env.su
        is_all_approver = user.has_groups('hr_expense.group_hr_expense_user,hr_expense.group_hr_expense_manager') or self.env.su

        valid_company_ids = set(self.env.companies.ids)
        expenses_employee_ids_under_user_ones = set()
        if is_team_approver:  # We don't need to search if the user has not the required rights
            expenses_employee_ids_under_user_ones = set(self.env['hr.employee'].sudo().search([
                ('id', 'in', self.employee_id.ids),
                ('id', 'child_of', user.employee_ids.ids),
                ('id', 'not in', user.employee_ids.ids),
            ]).ids)

        for expense in self:
            expense.can_reset = (
                expense.company_id.id in valid_company_ids
                and (
                        is_all_approver
                        or expense.employee_id.id in expenses_employee_ids_under_user_ones
                        or expense.employee_id.expense_manager_id == user
                        or (expense.state in {'draft', 'submitted'} and expense.employee_id.user_id == user)
                )
            )