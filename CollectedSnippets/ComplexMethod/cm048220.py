def _prepare_payments_vals(self):
        self.ensure_one()

        journal = self.journal_id
        payment_method_line = self.payment_method_line_id
        if not payment_method_line:
            raise UserError(_("You need to add a manual payment method on the journal (%s)", journal.name))

        AccountTax = self.env['account.tax']
        rate = abs(self.total_amount_currency / self.total_amount) if self.total_amount else 0.0
        base_line = self._prepare_base_line_for_taxes_computation(
            price_unit=self.total_amount_currency,
            quantity=1.0,
            account_id=self._get_base_account(),
            rate=rate,
        )
        base_lines = [base_line]
        AccountTax._add_tax_details_in_base_lines(base_lines, self.company_id)
        AccountTax._round_base_lines_tax_details(base_lines, self.company_id)
        AccountTax._add_accounting_data_in_base_lines_tax_details(base_lines, self.company_id, include_caba_tags=self.payment_mode == 'company_account')
        tax_results = AccountTax._prepare_tax_lines(base_lines, self.company_id)

        # Base line.
        move_lines = []
        base_move_line = {}
        for base_line, to_update in tax_results['base_lines_to_update']:
            base_move_line = {
                'name': self._get_move_line_name(),
                'account_id': base_line['account_id'].id,
                'product_id': base_line['product_id'].id,
                'analytic_distribution': base_line['analytic_distribution'],
                'expense_id': self.id,
                'tax_ids': [Command.set(base_line['tax_ids'].ids)],
                'tax_tag_ids': to_update['tax_tag_ids'],
                'amount_currency': to_update['amount_currency'],
                'balance': to_update['balance'],
                'currency_id': base_line['currency_id'].id,
                'partner_id': self.vendor_id.id,
            }
            move_lines.append(base_move_line)

        # Tax lines.
        total_tax_line_balance = 0.0
        for tax_line in tax_results['tax_lines_to_add']:
            total_tax_line_balance += tax_line['balance']
            move_lines.append(tax_line)
        base_move_line['balance'] = self.total_amount - total_tax_line_balance

        # Outstanding payment line.
        move_lines.append({
            'name': self._get_move_line_name(),
            'account_id': self._get_expense_account_destination(),
            'balance': -self.total_amount,
            'amount_currency': self.currency_id.round(-self.total_amount_currency),
            'currency_id': self.currency_id.id,
            'partner_id': self.vendor_id.id,
        })
        payment_vals = {
            'date': self.date,
            'memo': self.name,
            'journal_id': journal.id,
            'amount': self.total_amount_currency,
            'payment_type': 'outbound',
            'partner_type': 'supplier',
            'partner_id': self.vendor_id.id,
            'currency_id': self.currency_id.id,
            'payment_method_line_id': payment_method_line.id,
            'company_id': self.company_id.id,
        }
        move_vals = {
            **self._prepare_move_vals(),
            'date': self.date or fields.Date.context_today(self),
            'ref': self.name,
            'journal_id': journal.id,
            'partner_id': self.vendor_id.id,
            'currency_id': self.currency_id.id,
            'company_id': self.company_id.id,
            'line_ids': [Command.create(line) for line in move_lines],
            'attachment_ids': [
                Command.create(attachment.copy_data({'res_model': 'account.move', 'res_id': False, 'raw': attachment.raw})[0])
                for attachment in self.attachment_ids]
        }
        return move_vals, payment_vals