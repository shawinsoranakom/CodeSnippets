def _cannot_close_session(self, bank_payment_method_diffs=None):
        """
        Add check in this method if you want to return or raise an error when trying to either post cash details
        or close the session. Raising an error will always redirect the user to the back end.
        It should return {'successful': False, 'message': str, 'redirect': bool} if we can't close the session
        """
        bank_payment_method_diffs = bank_payment_method_diffs or {}
        if any(order.state == 'draft' for order in self.get_session_orders()):
            return {'successful': False, 'message': _("You cannot close the POS while there are still draft orders for the day."), 'redirect': False}
        if self.state == 'closed':
            return {
                'successful': False,
                'type': 'alert',
                'title': 'Session already closed',
                'message': _("The session has been already closed by another User. "
                            "All sales completed in the meantime have been saved in a "
                            "Rescue Session, which can be reviewed anytime and posted "
                            "to Accounting from Point of Sale's dashboard."),
                'redirect': True
            }
        if bank_payment_method_diffs:
            no_loss_account = self.env['account.journal']
            no_profit_account = self.env['account.journal']
            for payment_method in self.env['pos.payment.method'].browse(bank_payment_method_diffs.keys()):
                journal = payment_method.journal_id
                compare_to_zero = self.currency_id.compare_amounts(bank_payment_method_diffs.get(payment_method.id), 0)
                if compare_to_zero == -1 and not journal.loss_account_id:
                    no_loss_account |= journal
                elif compare_to_zero == 1 and not journal.profit_account_id:
                    no_profit_account |= journal
            message = ''
            if no_loss_account:
                message += _("Need loss account for the following journals to post the lost amount: %s\n", ', '.join(no_loss_account.mapped('name')))
            if no_profit_account:
                message += _("Need profit account for the following journals to post the gained amount: %s", ', '.join(no_profit_account.mapped('name')))
            if message:
                return {'successful': False, 'message': message, 'redirect': False}