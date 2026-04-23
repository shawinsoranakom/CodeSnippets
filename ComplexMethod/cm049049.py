def _compute_qty_to_invoice(self):
        """
        Compute the quantity to invoice. If the invoice policy is order, the quantity to invoice is
        calculated from the ordered quantity. Otherwise, the quantity delivered is used.
        For combo product lines, compute the value if a linked combo item line gets recomputed,
        and set `qty_to_invoice` only if at least one of its combo item lines is invoiceable.
        """
        combo_lines = set()
        for line in self:
            if line.state == 'sale' and not line.display_type:
                if line.product_id.type == 'combo':
                    combo_lines.add(line)
                elif line.product_id.invoice_policy == 'order':
                    line.qty_to_invoice = line.product_uom_qty - line.qty_invoiced
                else:
                    line.qty_to_invoice = line.qty_delivered - line.qty_invoiced
                if line.combo_item_id and line.linked_line_id:
                    combo_lines.add(line.linked_line_id)
            else:
                line.qty_to_invoice = 0
        for combo_line in combo_lines:
            if any(
                line.combo_item_id and line.qty_to_invoice
                for line in combo_line.linked_line_ids
            ):
                combo_line.qty_to_invoice = combo_line.product_uom_qty - combo_line.qty_invoiced
            else:
                combo_line.qty_to_invoice = 0