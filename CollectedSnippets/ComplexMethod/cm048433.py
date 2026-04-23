def _synchronize_quant(self, quantity, location, action="available", in_date=False, **quants_value):
        """ quantity should be express in product's UoM"""
        lot = quants_value.get('lot', self.lot_id)
        package = quants_value.get('package', self.package_id)
        owner = quants_value.get('owner', self.owner_id)
        available_qty = 0
        if not self.product_id.is_storable or self.product_uom_id.is_zero(quantity):
            return 0, False
        if action == "available":
            available_qty, in_date = self.env['stock.quant']._update_available_quantity(self.product_id, location, quantity, lot_id=lot, package_id=package, owner_id=owner, in_date=in_date)
        elif action == "reserved" and not self.move_id._should_bypass_reservation(location):
            self.env['stock.quant']._update_reserved_quantity(self.product_id, location, quantity, lot_id=lot, package_id=package, owner_id=owner)
        if available_qty < 0 and lot:
            # see if we can compensate the negative quants with some untracked quants
            untracked_qty = self.env['stock.quant']._get_available_quantity(self.product_id, location, lot_id=False, package_id=package, owner_id=owner, strict=True)
            if not untracked_qty:
                return available_qty, in_date
            taken_from_untracked_qty = min(untracked_qty, abs(quantity))
            self.env['stock.quant']._update_available_quantity(self.product_id, location, -taken_from_untracked_qty, lot_id=False, package_id=package, owner_id=owner, in_date=in_date)
            self.env['stock.quant']._update_available_quantity(self.product_id, location, taken_from_untracked_qty, lot_id=lot, package_id=package, owner_id=owner, in_date=in_date)
        return available_qty, in_date