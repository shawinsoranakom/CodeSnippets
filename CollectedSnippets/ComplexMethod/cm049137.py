def write(self, vals):
        values = vals
        if 'display_type' in values and self.filtered(lambda line: line.display_type != values.get('display_type')):
            raise UserError(_("You cannot change the type of a purchase order line. Instead you should delete the current line and create a new line of the proper type."))

        if 'product_qty' in values:
            precision = self.env['decimal.precision'].precision_get('Product Unit')
            for line in self:
                if (
                    line.order_id.state == "purchase"
                    and float_compare(line.product_qty, values["product_qty"], precision_digits=precision) != 0
                ):
                    line.order_id.message_post_with_source(
                        'purchase.track_po_line_template',
                        render_values={'line': line, 'product_qty': values['product_qty']},
                        subtype_xmlid='mail.mt_note',
                    )

        if 'qty_received' in values:
            for line in self:
                line._track_qty_received(values['qty_received'])
        return super().write(values)