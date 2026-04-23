def _compute_is_editable(self):
        is_hr_admin = (
            self.env.user.has_group('hr_expense.group_hr_expense_manager')
            or self.env.su
        )
        is_team_approver = self.env.user.has_group('hr_expense.group_hr_expense_team_approver')
        is_all_approver = self.env.user.has_group('hr_expense.group_hr_expense_user')

        expenses_employee_ids_under_user_ones = set()
        if is_team_approver:
            expenses_employee_ids_under_user_ones = set(
                self.env['hr.employee'].sudo().search(
                    [
                        ('id', 'in', self.employee_id.ids),
                        ('id', 'child_of', self.env.user.employee_ids.ids),
                        ('id', 'not in', self.env.user.employee_ids.ids),
                    ]
                ).ids
            )
        for expense in self:
            if (
                not expense.company_id
                or (expense.state not in {'draft', 'submitted', 'approved'} and not self.env.su)
            ):
                # When emptying the required company_id field, onchanges are triggered.
                # To avoid recomputing the interface without a company (which could
                # temporarily make fields editable), we do not recompute anything and wait
                # for a proper company to be set. The interface is also made not editable
                # when the state is not draft/submitted/approved and the user is not a superuser.
                expense.is_editable = False
                continue

            if is_hr_admin:
                # Administrator-level users are not restricted, they can edit their own expenses
                expense.is_editable = True
                continue

            employee = expense.employee_id
            is_own_expense = employee.user_id == self.env.user
            if is_own_expense and expense.state == 'draft':
                # Anyone can edit their own draft expense
                expense.is_editable = True
                continue

            managers = (
                expense.manager_id
                | employee.expense_manager_id
                | employee.sudo().department_id.manager_id.user_id.sudo(self.env.su)
            )
            if is_all_approver:
                managers |= self.env.user
            if expense.employee_id.id in expenses_employee_ids_under_user_ones:
                    managers |= self.env.user
            if not is_own_expense and self.env.user in managers:
                # If Approver-level or designated manager, can edit other people expense
                expense.is_editable = True
                continue
            expense.is_editable = False