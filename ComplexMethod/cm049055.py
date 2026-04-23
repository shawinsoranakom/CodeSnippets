def create(self, vals_list):
        for vals in vals_list:
            if vals.get('display_type') or self.default_get(['display_type']).get('display_type'):
                vals['product_uom_qty'] = 0.0

            if 'technical_price_unit' in vals and 'price_unit' not in vals:
                # price_unit field was set as readonly in the view (but technical_price_unit not)
                # the field is not sent by the client and expected to be recomputed, but isn't
                # because technical_price_unit is set.
                vals.pop('technical_price_unit')

        lines = super().create(vals_list)
        for line in lines:
            linked_line = line._get_linked_line()
            if linked_line:
                line.linked_line_id = linked_line
        if self.env.context.get('sale_no_log_for_new_lines'):
            return lines

        for line in lines:
            if line.product_id and line.state == 'sale':
                msg = _("Extra line with %s", line.product_id.display_name)
                line.order_id.message_post(body=msg)

        return lines