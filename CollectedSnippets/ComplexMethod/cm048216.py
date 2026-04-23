def update_activities_and_mails(self):
        """ Update the "Review this expense" activity with the new state of the expense, also sends mail to approver to ask them to act """
        expenses_activity_done = self.env['hr.expense']
        expenses_activity_unlink = self.env['hr.expense']
        expenses_submitted_to_review = self.env['hr.expense']
        for expense in self:
            if expense.state == 'submitted':
                expense.with_context(mail_activity_quick_update=True).activity_schedule(
                    'hr_expense.mail_act_expense_approval',
                    user_id=expense.manager_id.id or
                    expense.sudo()._get_default_responsible_for_approval().id or
                    self.env.user.id
                )
                expenses_submitted_to_review |= expense
            elif expense.state == 'approved':
                expenses_activity_done |= expense
            elif expense.state in {'draft', 'refused'}:
                expenses_activity_unlink |= expense

        # Batched actions
        if expenses_activity_done:
            expenses_activity_done.activity_feedback(['hr_expense.mail_act_expense_approval'])
        if expenses_activity_unlink:
            expenses_activity_unlink.activity_unlink(['hr_expense.mail_act_expense_approval'])

        # TODO: Remove in master
        # Note: field latest_version of model ir.module.module is the installed version
        installed_module_version = self.sudo().env.ref('base.module_hr_expense').latest_version
        if expenses_submitted_to_review and parse_version(installed_module_version)[2:] < parse_version('2.1'):
            self._send_submitted_expenses_mail()