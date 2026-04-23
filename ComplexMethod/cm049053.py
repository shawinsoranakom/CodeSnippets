def _compute_product_updatable(self):
        self.product_updatable = True
        for line in self:
            if (
                line.is_downpayment
                or line.state == 'cancel'
                or line.state == 'sale' and (
                    line.order_id.locked
                    or line.qty_invoiced > 0
                    or line.qty_delivered > 0
                )
            ):
                line.product_updatable = False