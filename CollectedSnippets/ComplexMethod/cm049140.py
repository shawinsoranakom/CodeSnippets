def _suggest_quantity(self):
        ''' Suggest a minimal quantity based on the seller
        '''
        if not self.product_id:
            return
        date = self.order_id.date_order and self.order_id.date_order.date() or fields.Date.context_today(self)
        seller_min_qty = self.product_id.seller_ids\
            .filtered(lambda r: r.partner_id == self.order_id.partner_id and
                      (not r.product_id or r.product_id == self.product_id) and
                      (not r.date_start or r.date_start <= date) and
                      (not r.date_end or r.date_end >= date))\
            .sorted(key=lambda r: r.min_qty)
        if seller_min_qty:
            self.product_qty = seller_min_qty[0].min_qty or 1.0
            self.product_uom_id = seller_min_qty[0].product_uom_id
        else:
            self.product_qty = 1.0