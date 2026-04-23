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