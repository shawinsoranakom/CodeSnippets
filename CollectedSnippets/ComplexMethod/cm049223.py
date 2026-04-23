def _get_filtered_sellers(self, partner_id=False, quantity=0.0, date=None, uom_id=False, params=False):
        self.ensure_one()
        if not date:
            date = fields.Date.context_today(self)
        precision = self.env['decimal.precision'].precision_get('Product Unit')

        sellers_filtered = self._prepare_sellers(params)
        sellers = self.env['product.supplierinfo']
        for seller in sellers_filtered:
            # Set quantity in UoM of seller
            quantity_uom_seller = quantity
            if quantity_uom_seller and uom_id and uom_id != seller.product_uom_id:
                quantity_uom_seller = uom_id._compute_quantity(quantity_uom_seller, seller.product_uom_id)

            if seller.date_start and seller.date_start > date:
                continue
            if seller.date_end and seller.date_end < date:
                continue
            if params and params.get('force_uom') and seller.product_uom_id != uom_id and seller.product_uom_id != self.uom_id:
                continue
            if partner_id and seller.partner_id not in [partner_id, partner_id.parent_id]:
                continue
            if quantity is not None and float_compare(quantity_uom_seller, seller.min_qty, precision_digits=precision) == -1:
                continue
            if seller.product_id and seller.product_id != self:
                continue
            sellers |= seller
        return sellers