def _set_quantity_done_prepare_vals(self, qty):
        def _move_qty(qty):
            return self.product_id.uom_id._compute_quantity(qty, self.product_uom, round=False)

        self.ensure_one()
        res = []
        qty = self.product_uom._compute_quantity(qty, self.product_id.uom_id, round=False)
        total_qty = qty
        consumed_quant = set()
        for ml in self.move_line_ids:
            ml_qty = ml.quantity
            if ml.product_uom_id.compare(ml_qty, 0) < 0:
                continue

            if ml.product_uom_id != self.product_id.uom_id:
                ml_qty = ml.product_uom_id._compute_quantity(ml_qty, self.product_id.uom_id, round=False)

            if self.product_uom.is_zero(_move_qty(qty)):
                res.append(Command.delete(ml.id))
                continue

            if ml.product_id.uom_id.compare(ml_qty, qty) > 0:
                if ml.product_uom_id != self.product_id.uom_id:
                    qty = ml.product_id.uom_id._compute_quantity(qty, ml.product_uom_id, round=False)
                res.append(Command.update(ml.id, {'quantity': qty}))
                qty = 0
                continue

            if ml.result_package_id:
                qty -= ml_qty
                continue
            # remove what already on the line
            taken_qty = min(qty, ml_qty)
            qty -= taken_qty
            if self.product_uom.compare(_move_qty(qty), 0) <= 0:
                continue

            # find a quant similar to the move line on which we can reserve
            ml_quants = self.env['stock.quant']._get_reserve_quantity(self.product_id,
                                                                      ml.location_id,
                                                                      qty,
                                                                      lot_id=ml.lot_id,
                                                                      package_id=ml.package_id,
                                                                      owner_id=ml.owner_id,
                                                                      strict=True)
            avail_qty = sum(q[1] for q in ml_quants)
            # the quant did not add the quantity reserved on this specific move line
            consumed_quant |= {q[0].id for q in ml_quants}
            if self.product_uom.compare(avail_qty, qty) <= 0:
                qty -= avail_qty  # decrease the target quantity for the next move lines
                avail_qty += ml_qty  # add the actual move line quantity as we will update it and not `+=` it
                if ml.product_uom_id != self.product_id.uom_id:
                    avail_qty = ml.product_id.uom_id._compute_quantity(avail_qty, ml.product_uom_id, round=False)
                res.append(Command.update(ml.id, {'quantity': avail_qty}))

        # First reserve on quants
        if self.product_uom.compare(_move_qty(qty), 0.0) > 0:
            quants = self.env['stock.quant']._get_reserve_quantity(self.product_id, self.location_id, total_qty)
            for quant, avail_qty in quants:
                if quant.id in consumed_quant:
                    continue
                # compare the stock move quantity with the product free quantity
                taken_qty = min(qty, avail_qty)
                qty -= taken_qty
                res.append(Command.create(self._prepare_move_line_vals(quantity=taken_qty, reserved_quant=quant)))
                if self.product_id.uom_id.compare(_move_qty(qty), 0.0) <= 0:
                    break

        # If quant is not enough, create a(some) move lines from the move itself
        if self.product_uom.compare(_move_qty(qty), 0.0) > 0:
            if self.product_id.tracking != 'serial':
                qty = _move_qty(qty)
                vals = self._prepare_move_line_vals(quantity=0)
                vals['quantity'] = qty
                res.append((0, 0, vals))
            else:
                for _i in range(0, int(qty)):
                    vals = self._prepare_move_line_vals(quantity=0)
                    vals['quantity'] = 1
                    vals['product_uom_id'] = self.product_id.uom_id.id
                    res.append((0, 0, vals))
        return res