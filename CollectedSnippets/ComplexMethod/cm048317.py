def _l10n_vn_edi_add_item_information(self, json_values):
        """ Create and return the items information for the current invoice. """
        self.ensure_one()
        items_information = []
        code_map = {
            'product': 1,
            'line_note': 2,
            'discount': 3,
        }
        discount_lines = self.invoice_line_ids._get_discount_lines()
        downpayment_lines = self.invoice_line_ids._get_downpayment_lines()
        for line in self.invoice_line_ids.filtered(lambda ln: ln.display_type in code_map):
            # For credit notes amount, we send negative values (reduces the amount of the original invoice)
            sign = 1 if self.move_type == 'out_invoice' else -1
            item_name = line.name.replace('\n', ' ')
            item_information = {
                'itemCode': line.product_id.code or '',
                'itemName': textwrap.shorten(item_name, width=500, placeholder='...'),
                'unitName': line.product_uom_id.name or 'Units',
                'unitPrice': line.currency_id.round(line.price_unit * sign),
                'quantity': line.quantity,
                # This amount should be without discount applied.
                'itemTotalAmountWithoutTax': line.currency_id.round(line.price_unit * line.quantity),
                # In Vietnam a line will always have only one tax.
                # Values are either: -2 (no tax), -1 (not declaring/paying taxes), 0,5,8,10 (the tax %)
                # Most use cases will be -2 or a tax percentage, so we limit the support to these.
                'taxPercentage': line.tax_ids and line.tax_ids[0].amount or -2,
                'taxAmount': line.currency_id.round(line.price_total - line.price_subtotal),
                'discount': line.discount,
                'itemTotalAmountAfterDiscount': line.price_subtotal,
                'itemTotalAmountWithTax': line.price_total,
                'selection': code_map[line.display_type],
            }
            if (
                line in discount_lines
                or line in downpayment_lines  # Downpayment lines are considered the same as discount lines
            ):
                item_information.update({
                    'selection': code_map['discount'],
                    'isIncreaseItem': False,
                    'unitPrice': abs(item_information['unitPrice']),
                    'quantity': abs(item_information['quantity']),
                    'itemTotalAmountWithoutTax': abs(item_information['itemTotalAmountWithoutTax']),
                    'itemTotalAmountAfterDiscount': abs(item_information['itemTotalAmountAfterDiscount']),
                    'itemTotalAmountWithTax': abs(item_information['itemTotalAmountWithTax']),
                })
            if self.move_type == 'out_refund':
                item_information.update({
                    'adjustmentTaxAmount': item_information['taxAmount'],
                    'isIncreaseItem': False,
                })
            if line.display_type == 'line_note':
                item_information = {'selection': item_information['selection'], 'itemName': item_information['itemName']}
            items_information.append(item_information)

        json_values['itemInfo'] = items_information