def _compute_sale_warning_text(self):
        if not self.env.user.has_group('sale.group_warning_sale'):
            self.sale_warning_text = ''
            return
        for order in self:
            warnings = OrderedSet()
            if partner_msg := order.partner_id.sale_warn_msg:
                warnings.add((order.partner_id.name or order.partner_id.display_name) + ' - ' + partner_msg)
            if partner_parent_msg := order.partner_id.parent_id.sale_warn_msg:
                parent = order.partner_id.parent_id
                warnings.add((parent.name or parent.display_name) + ' - ' + partner_parent_msg)
            for line in order.order_line:
                if product_msg := line.sale_line_warn_msg:
                    warnings.add(line.product_id.display_name + ' - ' + product_msg)
            order.sale_warning_text = '\n'.join(warnings)