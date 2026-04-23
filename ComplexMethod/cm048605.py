def _prepare_move_lines_per_type(self, write_off_line_vals=None, force_balance=None):
        ''' Prepare the dictionary containing default vals for account.move.lines for the current payment.
        returns a dictionary of list of python dictionary containing liquidity, counterpart and writeoff lines.
            E.g.
            {
                'liquidity_lines': [...],
                'counterpart_lines': [...],
                'writeoff_lines': [...],
            }
        '''
        self.ensure_one()

        if not self.outstanding_account_id:
            raise UserError(_(
                "You can't create a new payment without an outstanding payments/receipts account set either on the company or the %(payment_method)s payment method in the %(journal)s journal.",
                payment_method=self.payment_method_line_id.name, journal=self.journal_id.display_name))

        # Compute a default label to set on the journal items.
        line_name = ''.join(x[1] for x in self._get_aml_default_display_name_list() if x[1])

        # Prepare write-off lines.
        write_off_lines = write_off_line_vals or []
        write_off_amount_currency = sum(x['amount_currency'] for x in write_off_lines)
        write_off_balance = sum(x['balance'] for x in write_off_lines)

        # Prepare withholding lines.
        withholding_lines = self._prepare_move_withholding_lines({})
        withholding_amount_currency = sum(x['amount_currency'] for x in withholding_lines)
        withholding_balance = sum(x['balance'] for x in withholding_lines)

        # We don't support to combine 'write_off_lines' and 'withholding_lines' together because the withholding lines are already
        # passed as parameter as write-off lines in '_synchronize_to_moves'.
        if withholding_lines and write_off_lines:
            write_off_lines = []
            write_off_amount_currency = 0.0
            write_off_balance = 0.0

        # Prepare liquidity lines.
        if self.payment_type == 'inbound':
            # Receive money.
            liquidity_amount_currency = self.amount
        elif self.payment_type == 'outbound':
            # Send money.
            liquidity_amount_currency = -self.amount
        else:
            liquidity_amount_currency = 0.0

        if not write_off_line_vals and force_balance is not None:
            sign = 1 if liquidity_amount_currency > 0 else -1
            liquidity_balance = sign * abs(force_balance)
        else:
            liquidity_balance = self.currency_id._convert(
                liquidity_amount_currency,
                self.company_id.currency_id,
                self.company_id,
                self.date,
            )
        liquidity_amount_currency -= withholding_amount_currency
        liquidity_balance -= withholding_balance

        liquidity_lines = self._prepare_move_liquidity_lines({
            'name': line_name,
            'balance': liquidity_balance,
            'amount_currency': liquidity_amount_currency,
        })

        # Prepare counterpart lines.
        counterpart_amount_currency = -liquidity_amount_currency - write_off_amount_currency - withholding_amount_currency
        counterpart_balance = -liquidity_balance - write_off_balance - withholding_balance
        counterpart_lines = self._prepare_move_counterpart_lines({
            'name': line_name,
            'balance': counterpart_balance,
            'amount_currency': counterpart_amount_currency,
        })

        return {
            'liquidity_lines': liquidity_lines,
            'counterpart_lines': counterpart_lines,
            'write_off_lines': write_off_lines,
            'withholding_lines': withholding_lines,
        }