def _prepare_invoice_lines(self, move_type):
        """ Prepare a list of orm commands containing the dictionaries to fill the
        'invoice_line_ids' field when creating an invoice.

        :return: A list of Command.create to fill 'invoice_line_ids' when calling account.move.create.
        """
        invoice_lines = []
        for order in self:
            line_values_list = order.with_context(invoicing=True)._prepare_tax_base_line_values()
            for line_values in line_values_list:
                line = line_values['record']
                invoice_lines_values = order._get_invoice_lines_values(line_values, line, move_type)
                invoice_lines.append((0, None, invoice_lines_values))

                is_percentage = order.pricelist_id and any(
                    order.pricelist_id.item_ids.filtered(
                        lambda rule: rule.compute_price == "percentage")
                )
                if is_percentage and float_compare(line.price_unit, line.product_id.lst_price, precision_rounding=order.currency_id.rounding) < 0:
                    invoice_lines.append((0, None, {
                        'name': _('Price discount from %(original_price)s to %(discounted_price)s',
                                original_price=float_repr(line.product_id.lst_price, order.currency_id.decimal_places),
                                discounted_price=float_repr(line.price_unit, order.currency_id.decimal_places)),
                        'display_type': 'line_note',
                    }))
                if line.customer_note:
                    invoice_lines.append((0, None, {
                        'name': line.customer_note,
                        'display_type': 'line_note',
                    }))
            if order.general_customer_note:
                invoice_lines.append((0, None, {
                    'name': order.general_customer_note,
                    'display_type': 'line_note',
                }))
        return invoice_lines