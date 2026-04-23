def _prepare_account_move_line(self, move=False):
        self.ensure_one()
        aml_currency = move and move.currency_id or self.currency_id
        date = move and move.date or fields.Date.today()

        res = {
            'display_type': self.display_type or 'product',
            'name': self.env['account.move.line']._get_journal_items_full_name(self.name, self.product_id.display_name),
            'product_id': self.product_id.id,
            'product_uom_id': self.product_uom_id.id,
            'quantity': -self.qty_to_invoice if move and move.move_type == 'in_refund' else self.qty_to_invoice,
            'discount': self.discount,
            'price_unit': self.currency_id._convert(self.price_unit, aml_currency, self.company_id, date, round=False),
            'tax_ids': [(6, 0, self.tax_ids.ids)],
            'purchase_line_id': self.id,
            'is_downpayment': self.is_downpayment,
        }
        if self.is_downpayment and self.invoice_lines:
            res['account_id'] = self.invoice_lines.account_id[:1].id
        return res