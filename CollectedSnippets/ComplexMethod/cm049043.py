def _compute_sale_warning_text(self):
        if not self.env.user.has_group('sale.group_warning_sale'):
            self.sale_warning_text = ''
            return
        for move in self:
            if move.move_type != 'out_invoice':
                move.sale_warning_text = ''
                continue
            warnings = OrderedSet()
            if partner_msg := move.partner_id.sale_warn_msg:
                warnings.add((move.partner_id.name or move.partner_id.display_name) + ' - ' + partner_msg)
            if partner_parent_msg := move.partner_id.parent_id.sale_warn_msg:
                parent = move.partner_id.parent_id
                warnings.add((parent.name or parent.display_name) + ' - ' + partner_parent_msg)
            for product in move.invoice_line_ids.product_id:
                if product_msg := product.sale_line_warn_msg:
                    warnings.add(product.display_name + ' - ' + product_msg)
            move.sale_warning_text = '\n'.join(warnings)