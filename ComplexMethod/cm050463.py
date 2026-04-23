def _create_invoice(self, move_vals):
        AccountMove = self.env['account.move']

        invoice = AccountMove.sudo()\
            .with_company(self.company_id)\
            .with_context(default_move_type=move_vals['move_type'], linked_to_pos=True)\
            .create(move_vals)
        currency = self.currency_id
        amount_total = sum(order.amount_total for order in self)
        payment_total = sum(order.amount_paid for order in self)

        if self.config_id.cash_rounding and invoice.invoice_cash_rounding_id:
            line_ids_commands = []
            rate = invoice.invoice_currency_rate
            sign = invoice.direction_sign
            amount_paid = (-1 if amount_total < 0.0 else 1) * payment_total
            difference_currency = sign * (amount_paid - invoice.amount_total)
            difference_balance = invoice.company_currency_id.round(difference_currency / rate) if rate else 0.0
            if not currency.is_zero(difference_currency):
                rounding_line = invoice.line_ids.filtered(lambda line: line.display_type == 'rounding' and not line.tax_line_id)
                if rounding_line:
                    line_ids_commands.append(Command.update(rounding_line.id, {
                        'amount_currency': rounding_line.amount_currency + difference_currency,
                        'balance': rounding_line.balance + difference_balance,
                    }))
                else:
                    if difference_currency > 0.0:
                        account = invoice.invoice_cash_rounding_id.loss_account_id
                    else:
                        account = invoice.invoice_cash_rounding_id.profit_account_id
                    line_ids_commands.append(Command.create({
                        'name': invoice.invoice_cash_rounding_id.name,
                        'amount_currency': difference_currency,
                        'balance': difference_balance,
                        'currency_id': invoice.currency_id.id,
                        'display_type': 'rounding',
                        'account_id': account.id,
                    }))
                existing_terms_line = invoice.line_ids\
                    .filtered(lambda line: line.display_type == 'payment_term')\
                    .sorted(lambda line: -abs(line.amount_currency))[:1]
                line_ids_commands.append(Command.update(existing_terms_line.id, {
                    'amount_currency': existing_terms_line.amount_currency - difference_currency,
                    'balance': existing_terms_line.balance - difference_balance,
                }))
                with AccountMove._check_balanced({'records': invoice}):
                    invoice.with_context(skip_invoice_sync=True).line_ids = line_ids_commands
        body = _("This invoice has been created from the point of sale session:%s",
                    Markup().join(Markup("%s ") % order._get_html_link() for order in self)
                )
        invoice.message_post(body=body)
        return invoice