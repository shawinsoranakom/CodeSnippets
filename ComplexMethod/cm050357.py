def _compute_purchase_warn_msg(self):
        self.purchase_warn_msg = ''
        # follows partner warning logic from PurchaseOrder
        if not self.env.user.has_group('purchase.group_warning_purchase'):
            return
        for partner in self.partner_ids:
            # If partner has no warning, check its company
            if not partner.purchase_warn_msg:
                partner = partner.parent_id
            if partner and partner.purchase_warn_msg:
                self.purchase_warn_msg = _("Warning for %(partner)s:\n%(warning_message)s\n", partner=partner.name, warning_message=partner.purchase_warn_msg)
            if self.copy_products and self.origin_po_id.order_line:
                for line in self.origin_po_id.order_line:
                    if line.product_id.purchase_line_warn_msg:
                        self.purchase_warn_msg += _("Warning for %(product)s:\n%(warning_message)s\n", product=line.product_id.name, warning_message=line.product_id.purchase_line_warn_msg)