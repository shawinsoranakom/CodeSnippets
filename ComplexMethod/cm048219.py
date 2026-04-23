def _get_cannot_approve_reason(self):
        """ Returns the reason why the user cannot approve the expense """
        is_team_approver = self.env.user.has_group('hr_expense.group_hr_expense_team_approver') or self.env.su
        is_approver = self.env.user.has_group('hr_expense.group_hr_expense_user') or self.env.su
        is_hr_admin = self.env.user.has_group('hr_expense.group_hr_expense_manager') or self.env.su

        valid_company_ids = set(self.env.companies.ids)

        expenses_employee_ids_under_user_ones = set()
        if is_team_approver:  # We don't need to search if the user has not the required rights
            expenses_employee_ids_under_user_ones = set(
                self.env['hr.employee'].sudo().search([
                    ('id', 'in', self.employee_id.ids),
                    ('id', 'child_of', self.env.user.employee_ids.ids),
                    ('id', 'not in', self.env.user.employee_ids.ids),
                ]).ids
            )
        reasons_per_record_id = {}
        for expense in self:
            reason = False
            expense_employee = expense.employee_id
            is_expense_team_approver = (
                    is_team_approver  # Admins are team approvers, not necessarily direct parents
                    or expense_employee.id in expenses_employee_ids_under_user_ones
                    or (expense_employee.expense_manager_id == self.env.user)
            )
            if expense.company_id.id not in valid_company_ids:
                reason = _(
                    "%(expense_name)s: Your are neither a Manager nor a HR Officer of this expense's company",
                    expense_name=expense.name,
                )

            elif not is_expense_team_approver:
                reason = _("%(expense_name)s: You are neither a Manager nor a HR Officer", expense_name=expense.name)

            elif not is_hr_admin:
                current_managers = (
                        expense_employee.expense_manager_id
                        | expense_employee.sudo().department_id.manager_id.user_id.sudo(self.env.su)
                        | expense.manager_id
                )
                if expense_employee.id in expenses_employee_ids_under_user_ones:
                    current_managers |= self.env.user

                if expense_employee.user_id == self.env.user:
                    reason = _("%(expense_name)s: It is your own expense", expense_name=expense.name)

                elif self.env.user not in current_managers and not is_approver:
                    reason = _("%(expense_name)s: It is not from your department", expense_name=expense.name)
            reasons_per_record_id[expense.id] = reason
        return reasons_per_record_id