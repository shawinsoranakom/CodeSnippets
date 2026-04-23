def _compute_state(self):
        """
        Compute the states of the expense as such (priority is given to the last matching state of the list):
            - draft: By default
            - submitted: When the approval_state is 'submitted'
            - approved: When the approval_state is 'approved'
            - refused: When the approval_state is 'refused'
            - paid: When it is a company paid expense or the move state is neither 'draft' nor 'posted'
            - in_payment (or paid): When the move state is 'posted' and it's 'payment_state' is 'in_payment' or 'paid'
                                    or ('partial' and there is a residual amount)
            - posted: When the linked move state is 'draft', or if it is 'posted' and it's 'payment_state' is 'not_paid'
        """
        for expense in self:
            move = expense.account_move_id
            if move.state == 'cancel':
                expense.state = 'paid'
                continue
            if move:
                if expense.payment_mode == 'company_account':
                    # Shortcut to paid, as it's already paid, but we may not have the bank statement yet
                    expense.state = 'paid'
                elif move.state == 'draft':
                    expense.state = 'posted'
                elif move.payment_state == 'not_paid':
                    expense.state = 'posted'
                elif (
                        move.payment_state == 'in_payment'
                        or (move.payment_state == 'partial' and not expense.company_currency_id.is_zero(expense.amount_residual))
                ):
                    expense.state = self.env['account.move']._get_invoice_in_payment_state()
                else:  # Partial, reversed or in_payment
                    expense.state = 'paid'
                continue
            expense.state = expense.approval_state or 'draft'