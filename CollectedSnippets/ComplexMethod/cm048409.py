def _onchange_location_or_product_id(self):
        vals = {}

        # Once the new line is complete, fetch the new theoretical values.
        if self.product_id and self.location_id:
            # Sanity check if a lot has been set.
            if self.lot_id:
                if self.tracking == 'none' or self.product_id != self.lot_id.product_id:
                    vals['lot_id'] = None

            quant = self._gather(
                self.product_id, self.location_id, lot_id=self.lot_id,
                package_id=self.package_id, owner_id=self.owner_id, strict=True)
            self.quantity = sum(quant.filtered(lambda q: q.lot_id == self.lot_id).mapped('quantity'))

            # Special case: directly set the quantity to one for serial numbers,
            # it'll trigger `inventory_quantity` compute.
            if self.lot_id and self.tracking == 'serial':
                vals['inventory_quantity'] = 1
                vals['inventory_quantity_auto_apply'] = 1

        if vals:
            self.update(vals)