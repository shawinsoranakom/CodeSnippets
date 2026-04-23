def _clean_reservations(self):
        reserved_quants = self.env['stock.quant']._read_group(
            [('reserved_quantity', '!=', 0)],
            ['product_id', 'location_id', 'lot_id', 'package_id', 'owner_id'],
            ['reserved_quantity:sum', 'id:recordset'],
        )
        reserved_move_lines = self.env['stock.move.line']._read_group(
            [
                ('state', 'in', ['assigned', 'partially_available', 'waiting', 'confirmed']),
                ('quantity_product_uom', '!=', 0),
                ('product_id.is_storable', '=', True),
            ],
            ['product_id', 'location_id', 'lot_id', 'package_id', 'owner_id'],
            ['quantity_product_uom:sum'],
        )
        reserved_move_lines = {
            (product, location, lot, package, owner): reserved_quantity
            for product, location, lot, package, owner, reserved_quantity in reserved_move_lines
        }
        for product, location, lot, package, owner, reserved_quantity, quants in reserved_quants:
            ml_reserved_qty = reserved_move_lines.get((product, location, lot, package, owner), 0)
            if location.should_bypass_reservation():
                quants._update_reserved_quantity(product, location, -reserved_quantity, lot_id=lot, package_id=package, owner_id=owner)
            elif product.uom_id.compare(reserved_quantity, ml_reserved_qty) != 0:
                quants._update_reserved_quantity(product, location, ml_reserved_qty - reserved_quantity, lot_id=lot, package_id=package, owner_id=owner)
            if ml_reserved_qty:
                del reserved_move_lines[(product, location, lot, package, owner)]

        for (product, location, lot, package, owner), reserved_quantity in reserved_move_lines.items():
            if location.should_bypass_reservation() or\
                self.env['stock.quant']._should_bypass_product(product, location, reserved_quantity, lot, package, owner):
                continue
            else:
                self.env['stock.quant']._update_reserved_quantity(product, location, reserved_quantity, lot_id=lot, package_id=package, owner_id=owner)