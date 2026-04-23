def _compute_purchase_warning_text(self):
        if not self.env.user.has_group('purchase.group_warning_purchase'):
            self.purchase_warning_text = ''
            return
        for move in self:
            if move.move_type != 'in_invoice':
                move.purchase_warning_text = ''
                continue
            warnings = OrderedSet()
            if partner_msg := move.partner_id.purchase_warn_msg:
                warnings.add((move.partner_id.name or move.partner_id.display_name) + ' - ' + partner_msg)
            if partner_parent_msg := move.partner_id.parent_id.purchase_warn_msg:
                parent = move.partner_id.parent_id
                warnings.add((parent.name or parent.display_name) + ' - ' + partner_parent_msg)
            for product in move.invoice_line_ids.product_id:
                if product_msg := product.purchase_line_warn_msg:
                    warnings.add(product.display_name + ' - ' + product_msg)
            move.purchase_warning_text = '\n'.join(warnings)