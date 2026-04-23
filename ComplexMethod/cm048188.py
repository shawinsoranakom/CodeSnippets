def _create_invoice(self, move_type='out_invoice', invoice_amount=50, currency_id=None, partner_id=None, date_invoice=None, payment_term_id=False, auto_validate=False, taxes=None, state=None):
        if move_type == 'entry':
            raise AssertionError("Unexpected move_type : 'entry'.")

        if not taxes:
            taxes = self.env['account.tax']

        date_invoice = date_invoice or time.strftime('%Y') + '-07-01'

        invoice_vals = {
            'move_type': move_type,
            'partner_id': partner_id or self.partner_agrolait.id,
            'invoice_date': date_invoice,
            'date': date_invoice,
            'invoice_line_ids': [Command.create({
                'name': 'product that cost %s' % invoice_amount,
                'quantity': 1,
                'price_unit': invoice_amount,
                'tax_ids': [Command.set(taxes.ids)],
            })]
        }

        if payment_term_id:
            invoice_vals['invoice_payment_term_id'] = payment_term_id

        if currency_id:
            invoice_vals['currency_id'] = currency_id

        invoice = self.env['account.move'].with_context(default_move_type=move_type).create(invoice_vals)

        if state == 'cancel':
            invoice.write({'state': 'cancel'})
        elif auto_validate or state == 'posted':
            invoice.action_post()
        return invoice