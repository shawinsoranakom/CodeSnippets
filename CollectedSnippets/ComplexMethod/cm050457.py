def _get_invoice_lines_values(self, line_values, pos_line, move_type):
        # correct quantity sign based on move type and if line is refund.
        is_refund_order = bool(
            pos_line.order_id.is_refund
            or pos_line.order_id.amount_total < 0.0
        )
        qty_sign = -1 if (
            (move_type == 'out_invoice' and is_refund_order)
            or (move_type == 'out_refund' and not is_refund_order)
        ) else 1

        if line_values['product_id'].type == 'combo':
            quantity = int(line_values['quantity']) if line_values['quantity'] == int(
                line_values['quantity']) else line_values['quantity']
            return {
                'display_type': 'line_section',
                'name': f"{line_values['product_id'].name} x {quantity}",
                'quantity': qty_sign * line_values['quantity'],
                'product_uom_id': line_values['uom_id'].id,
            }

        return {
            'product_id': line_values['product_id'].id,
            'quantity': qty_sign * line_values['quantity'],
            'discount': line_values['discount'],
            'price_unit': line_values['price_unit'],
            'name': line_values['name'],
            'tax_ids': [(6, 0, line_values['tax_ids'].ids)],
            'product_uom_id': line_values['uom_id'].id,
            'extra_tax_data': self.env['account.tax']._export_base_line_extra_tax_data(line_values),
        }