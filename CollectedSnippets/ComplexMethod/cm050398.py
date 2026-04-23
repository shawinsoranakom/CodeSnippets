def _compute_qty_to_deliver(self):
        """Compute the visibility of the inventory widget."""
        for line in self:
            line.qty_to_deliver = line.product_uom_qty - line.qty_delivered
            if line.state in ('draft', 'sent', 'sale') and line.is_storable and line.product_uom_id and line.qty_to_deliver > 0:
                if line.state == 'sale' and all(m.state in ['done', 'cancel'] for m in line.move_ids):
                    line.display_qty_widget = False
                else:
                    line.display_qty_widget = True
            else:
                line.display_qty_widget = False