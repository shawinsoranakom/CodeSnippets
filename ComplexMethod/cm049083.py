def _set_value(self, correction_quantity=None):
        """Set the value of the move.

        :param correction_quantity: if set, it means that the quantity of the move has been
            changed by this amount (can be positive or negative). In that case, we just update
            the value of the move based on the ratio of extra_quantity / quantity. It only applies
            on out_move since their value is computed during action_done, and it's used to get a
            more accurate value for COGS. In case of in move correction, you have to call _set_value
            without arguments.
        """
        products_to_recompute = set()
        lots_to_recompute = set()
        fifo_qty_processed = defaultdict(float)

        for move in self:
            # Incoming moves
            if move.is_dropship or move.is_in:
                products_to_recompute.add(move.product_id.id)
                if move.product_id.lot_valuated:
                    if any(not ml.lot_id for ml in move.move_line_ids):
                        raise UserError(self.env._(
                            "A lot/serial number is required for product '%s' as it has lot valuation enabled.",
                            move.product_id.display_name))
                    lots_to_recompute.update(move.move_line_ids.lot_id.ids)
            if move.is_in:
                move.value = move.sudo()._get_value()
                continue
            # Outgoing moves
            if not move._is_out():
                continue
            if correction_quantity:
                previous_qty = move.quantity - correction_quantity
                ratio = correction_quantity / previous_qty if previous_qty else 0
                move.value += ratio * move.value
                continue
            if move.product_id.lot_valuated:
                value = 0.0
                for move_line in move.move_line_ids:
                    if move_line.lot_id:
                        value += move_line.lot_id.standard_price * move_line.quantity_product_uom
                    else:
                        value += move.product_id.standard_price * move_line.quantity_product_uom
                move.value = value
                continue

            if move.product_id.cost_method == 'fifo':
                valued_qty = move._get_valued_qty()
                move.value = move.product_id.with_context(fifo_qty_already_processed=fifo_qty_processed[move.product_id])._run_fifo(valued_qty)
                fifo_qty_processed[move.product_id] += valued_qty
            else:
                move.value = move.product_id.standard_price * move._get_valued_qty()

        # Recompute the standard price
        self.env['product.product'].browse(products_to_recompute)._update_standard_price()
        self.env['stock.lot'].browse(lots_to_recompute)._update_standard_price()