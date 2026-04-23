def _get_reserve_quantity(self, product_id, location_id, quantity, uom_id=None, lot_id=None, package_id=None, owner_id=None, strict=False):
        """ Get the quantity available to reserve for the set of quants
        sharing the combination of `product_id, location_id` if `strict` is set to False or sharing
        the *exact same characteristics* otherwise. If no quants are in self, `_gather` will do a search to fetch the quants
        Typically, this method is called before the `stock.move.line` creation to know the reserved_qty that could be use.
        It's also called by `_update_reserve_quantity` to find the quant to reserve.

        :return: a list of tuples (quant, quantity_reserved) showing on which quant the reservation
            could be done and how much the system is able to reserve on it
        """
        self = self.sudo()

        quants = self._gather(product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=strict, qty=quantity)

        # avoid quants with negative qty to not lower available_qty
        available_quantity = quants._get_available_quantity(product_id, location_id, lot_id, package_id, owner_id, strict)

        # do full packaging reservation when it's needed
        if self.env.context.get('packaging_uom_id') and product_id.product_tmpl_id.categ_id.packaging_reserve_method == "full":
            available_quantity = self.env.context.get('packaging_uom_id')._check_qty(available_quantity, product_id.uom_id, "DOWN")

        quantity = min(quantity, available_quantity)

        # `quantity` is in the quants unit of measure. There's a possibility that the move's
        # unit of measure won't be respected if we blindly reserve this quantity, a common usecase
        # is if the move's unit of measure's rounding does not allow fractional reservation. We chose
        # to convert `quantity` to the move's unit of measure with a down rounding method and
        # then get it back in the quants unit of measure with an half-up rounding_method. This
        # way, we'll never reserve more than allowed. We do not apply this logic if
        # `available_quantity` is brought by a chained move line. In this case, `_prepare_move_line_vals`
        # will take care of changing the UOM to the UOM of the product.
        if not strict and uom_id and product_id.uom_id != uom_id:
            quantity_move_uom = product_id.uom_id._compute_quantity(quantity, uom_id, rounding_method='DOWN')
            quantity = uom_id._compute_quantity(quantity_move_uom, product_id.uom_id, rounding_method='HALF-UP')

        if product_id.tracking == 'serial':
            if product_id.uom_id.compare(quantity, int(quantity)) != 0:
                quantity = 0

        reserved_quants = []

        if product_id.uom_id.compare(quantity, 0) > 0:
            # if we want to reserve
            available_quantity = sum(quants.filtered(lambda q: product_id.uom_id.compare(q.quantity, 0) > 0).mapped('quantity')) - sum(quants.mapped('reserved_quantity'))
        elif product_id.uom_id.compare(quantity, 0) < 0:
            # if we want to unreserve
            available_quantity = sum(quants.mapped('reserved_quantity'))
            if product_id.uom_id.compare(abs(quantity), available_quantity) > 0:
                raise UserError(_('It is not possible to unreserve more products of %s than you have in stock.', product_id.display_name))
        else:
            return reserved_quants

        negative_reserved_quantity = defaultdict(float)
        for quant in quants:
            if product_id.uom_id.compare(quant.quantity - quant.reserved_quantity, 0) < 0:
                negative_reserved_quantity[(quant.location_id, quant.lot_id, quant.package_id, quant.owner_id)] += quant.quantity - quant.reserved_quantity
        for quant in quants:
            if product_id.uom_id.compare(quantity, 0) > 0:
                max_quantity_on_quant = quant.quantity - quant.reserved_quantity
                if product_id.uom_id.compare(max_quantity_on_quant, 0) <= 0:
                    continue
                negative_quantity = negative_reserved_quantity[(quant.location_id, quant.lot_id, quant.package_id, quant.owner_id)]
                if negative_quantity:
                    negative_qty_to_remove = min(abs(negative_quantity), max_quantity_on_quant)
                    negative_reserved_quantity[(quant.location_id, quant.lot_id, quant.package_id, quant.owner_id)] += negative_qty_to_remove
                    max_quantity_on_quant -= negative_qty_to_remove
                if product_id.uom_id.compare(max_quantity_on_quant, 0) <= 0:
                    continue
                max_quantity_on_quant = min(max_quantity_on_quant, quantity)
                reserved_quants.append((quant, max_quantity_on_quant))
                quantity -= max_quantity_on_quant
                available_quantity -= max_quantity_on_quant
            else:
                max_quantity_on_quant = min(quant.reserved_quantity, abs(quantity))
                reserved_quants.append((quant, -max_quantity_on_quant))
                quantity += max_quantity_on_quant
                available_quantity += max_quantity_on_quant

            if product_id.uom_id.is_zero(quantity) or product_id.uom_id.is_zero(available_quantity):
                break
        return reserved_quants