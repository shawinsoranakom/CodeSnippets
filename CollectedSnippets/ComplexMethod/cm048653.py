def _recompute_cash_rounding_lines(self):
        ''' Handle the cash rounding feature on invoices.

        In some countries, the smallest coins do not exist. For example, in Switzerland, there is no coin for 0.01 CHF.
        For this reason, if invoices are paid in cash, you have to round their total amount to the smallest coin that
        exists in the currency. For the CHF, the smallest coin is 0.05 CHF.

        There are two strategies for the rounding:

        1) Add a line on the invoice for the rounding: The cash rounding line is added as a new invoice line.
        2) Add the rounding in the biggest tax amount: The cash rounding line is added as a new tax line on the tax
        having the biggest balance.
        '''
        self.ensure_one()
        def _compute_cash_rounding(self, total_amount_currency):
            ''' Compute the amount differences due to the cash rounding.
            :param self:                    The current account.move record.
            :param total_amount_currency:   The invoice's total in invoice's currency.
            :return:                        The amount differences both in company's currency & invoice's currency.
            '''
            difference = self.invoice_cash_rounding_id.compute_difference(self.currency_id, total_amount_currency)
            if self.currency_id == self.company_id.currency_id:
                diff_amount_currency = diff_balance = difference
            else:
                diff_amount_currency = difference
                diff_balance = self.currency_id._convert(diff_amount_currency, self.company_id.currency_id, self.company_id, self.invoice_date or self.date)
            return diff_balance, diff_amount_currency

        def _apply_cash_rounding(self, diff_balance, diff_amount_currency, cash_rounding_line):
            ''' Apply the cash rounding.
            :param self:                    The current account.move record.
            :param diff_balance:            The computed balance to set on the new rounding line.
            :param diff_amount_currency:    The computed amount in invoice's currency to set on the new rounding line.
            :param cash_rounding_line:      The existing cash rounding line.
            :return:                        The newly created rounding line.
            '''
            rounding_line_vals = {
                'balance': diff_balance,
                'amount_currency': diff_amount_currency,
                'partner_id': self.partner_id.id,
                'move_id': self.id,
                'currency_id': self.currency_id.id,
                'company_id': self.company_id.id,
                'company_currency_id': self.company_id.currency_id.id,
                'display_type': 'rounding',
            }

            if self.invoice_cash_rounding_id.strategy == 'biggest_tax':
                biggest_tax_line = None
                for tax_line in self.line_ids.filtered('tax_repartition_line_id'):
                    if not biggest_tax_line or abs(tax_line.balance) > abs(biggest_tax_line.balance):
                        biggest_tax_line = tax_line

                # No tax found.
                if not biggest_tax_line:
                    return

                rounding_line_vals.update({
                    'name': _("%(tax_name)s (rounding)", tax_name=biggest_tax_line.name),
                    'account_id': biggest_tax_line.account_id.id,
                    'tax_repartition_line_id': biggest_tax_line.tax_repartition_line_id.id,
                    'tax_tag_ids': [(6, 0, biggest_tax_line.tax_tag_ids.ids)],
                    'tax_ids': [Command.set(biggest_tax_line.tax_ids.ids)]
                })

            elif self.invoice_cash_rounding_id.strategy == 'add_invoice_line':
                if diff_balance > 0.0 and self.invoice_cash_rounding_id.loss_account_id:
                    account_id = self.invoice_cash_rounding_id.loss_account_id.id
                else:
                    account_id = self.invoice_cash_rounding_id.profit_account_id.id
                rounding_line_vals.update({
                    'name': self.invoice_cash_rounding_id.name,
                    'account_id': account_id,
                    'tax_ids': [Command.clear()]
                })

            # Create or update the cash rounding line.
            if cash_rounding_line:
                cash_rounding_line.write(rounding_line_vals)
            else:
                cash_rounding_line = self.env['account.move.line'].create(rounding_line_vals)

        existing_cash_rounding_line = self.line_ids.filtered(lambda line: line.display_type == 'rounding')

        # The cash rounding has been removed.
        if not self.invoice_cash_rounding_id:
            existing_cash_rounding_line.unlink()
            # self.line_ids -= existing_cash_rounding_line
            return

        # The cash rounding strategy has changed.
        if self.invoice_cash_rounding_id and existing_cash_rounding_line:
            strategy = self.invoice_cash_rounding_id.strategy
            old_strategy = 'biggest_tax' if existing_cash_rounding_line.tax_line_id else 'add_invoice_line'
            if strategy != old_strategy:
                # self.line_ids -= existing_cash_rounding_line
                existing_cash_rounding_line.unlink()
                existing_cash_rounding_line = self.env['account.move.line']

        others_lines = self.line_ids.filtered(lambda line: line.account_id.account_type not in ('asset_receivable', 'liability_payable'))
        others_lines -= existing_cash_rounding_line
        total_amount_currency = sum(others_lines.mapped('amount_currency'))

        diff_balance, diff_amount_currency = _compute_cash_rounding(self, total_amount_currency)

        # The invoice is already rounded.
        if self.currency_id.is_zero(diff_balance) and self.currency_id.is_zero(diff_amount_currency):
            existing_cash_rounding_line.unlink()
            # self.line_ids -= existing_cash_rounding_line
            return

        # No update needed
        if existing_cash_rounding_line \
            and float_compare(existing_cash_rounding_line.balance, diff_balance, precision_rounding=self.currency_id.rounding) == 0 \
            and float_compare(existing_cash_rounding_line.amount_currency, diff_amount_currency, precision_rounding=self.currency_id.rounding) == 0:
            return

        _apply_cash_rounding(self, diff_balance, diff_amount_currency, existing_cash_rounding_line)