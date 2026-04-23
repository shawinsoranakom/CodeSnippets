def _prepare_invoice_line(self, **optional_values):
        """Prepare the values to create the new invoice line for a sales order line.

        :param optional_values: any parameter that should be added to the returned invoice line
        :rtype: dict
        """
        self.ensure_one()

        if self.product_id.type == 'combo':
            # If the quantity to invoice is a whole number, format it as an integer (with no decimal point)
            qty_to_invoice = int(self.qty_to_invoice) if self.qty_to_invoice == int(self.qty_to_invoice) else self.qty_to_invoice
            return {
                'display_type': 'line_section',
                'sequence': self.sequence,
                'name': f'{self.product_id.name} x {qty_to_invoice}',
                'product_uom_id': self.product_uom_id.id,
                'quantity': self.qty_to_invoice,
                'sale_line_ids': [Command.link(self.id)],
                'collapse_prices': self.collapse_prices,
                'collapse_composition': self.collapse_composition,
                **optional_values,
            }
        res = {
            'display_type': self.display_type or 'product',
            'sequence': self.sequence,
            'name': self.env['account.move.line']._get_journal_items_full_name(self.name, self.product_id.display_name),
            'product_id': self.product_id.id,
            'product_uom_id': self.product_uom_id.id,
            'quantity': self.qty_to_invoice,
            'discount': self.discount,
            'price_unit': self.price_unit,
            'tax_ids': [Command.set(self.tax_ids.ids)],
            'sale_line_ids': [Command.link(self.id)],
            'is_downpayment': self.is_downpayment,
            'extra_tax_data': self.extra_tax_data,
            'collapse_prices': self.collapse_prices,
            'collapse_composition': self.collapse_composition,
        }
        downpayment_lines = self.invoice_lines.filtered('is_downpayment')
        if self.is_downpayment and downpayment_lines:
            res['account_id'] = downpayment_lines.account_id[:1].id
        if optional_values:
            res.update(optional_values)
        if self.display_type:
            res['account_id'] = False
        return res