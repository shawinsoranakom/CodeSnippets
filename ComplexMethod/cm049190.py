def _create_payment_vals_from_wizard(self, batch_result):
        """
        Update the computation of the payment vals in order to correctly set the outstanding account as well as the
        withholding line when needed.
        """
        # EXTEND 'account'
        payment_vals = super()._create_payment_vals_from_wizard(batch_result)

        if not self.withholding_line_ids or not self.should_withhold_tax:
            return payment_vals

        if self.withholding_net_amount < 0:
            raise UserError(self.env._("The withholding net amount cannot be negative."))

        # Prepare the withholding lines.
        withholding_account = self.withholding_outstanding_account_id
        if withholding_account:
            payment_vals['outstanding_account_id'] = withholding_account.id
            if not withholding_account.reconcile and withholding_account.account_type not in ('asset_cash', 'liability_credit_card', 'off_balance'):
                withholding_account.reconcile = True
        payment_vals['should_withhold_tax'] = self.should_withhold_tax
        payment_vals['withholding_line_ids'] = []
        for withholding_line_values in self.withholding_line_ids.with_context(active_test=False).copy_data():
            del withholding_line_values['payment_register_id']
            del withholding_line_values['placeholder_value']
            payment_vals['withholding_line_ids'].append(Command.create(withholding_line_values))
        return payment_vals