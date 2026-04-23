def _update_available_quantity(self, product_id, location_id, quantity=False, reserved_quantity=False, lot_id=None, package_id=None, owner_id=None, in_date=None):
        """ Increase or decrease `quantity` or 'reserved quantity' of a set of quants for a given set of
        product_id/location_id/lot_id/package_id/owner_id.

        :param product_id:
        :param location_id:
        :param quantity:
        :param lot_id:
        :param package_id:
        :param owner_id:
        :param datetime in_date: Should only be passed when calls to this method are done in
                                 order to move a quant. When creating a tracked quant, the
                                 current datetime will be used.
        :return: tuple (available_quantity, in_date as a datetime)
        """
        if not (quantity or reserved_quantity):
            raise ValidationError(_('Quantity or Reserved Quantity should be set.'))
        self = self.sudo()
        quants = self._gather(product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=True)
        if lot_id:
            if product_id.uom_id.compare(quantity, 0) > 0:
                quants = quants.filtered(lambda q: q.lot_id)
            else:
                # Don't remove quantity from a negative quant without lot
                quants = quants.filtered(lambda q: product_id.uom_id.compare(q.quantity, 0) > 0 or q.lot_id)

        if location_id.should_bypass_reservation():
            incoming_dates = []
        else:
            incoming_dates = [quant.in_date for quant in quants if quant.in_date and
                              quant.product_uom_id.compare(quant.quantity, 0) > 0]
        if in_date:
            incoming_dates += [in_date]
        # If multiple incoming dates are available for a given lot_id/package_id/owner_id, we
        # consider only the oldest one as being relevant.
        if incoming_dates:
            in_date = min(incoming_dates)
        else:
            in_date = fields.Datetime.now()

        quant = None
        if quants:
            # quants are already ordered in _gather
            # lock the first available
            quant = quants.try_lock_for_update(allow_referencing=True, limit=1)

        if quant:
            vals = {'in_date': in_date}
            if quantity:
                vals['quantity'] = quant.quantity + quantity
            if reserved_quantity:
                vals['reserved_quantity'] = max(0, quant.reserved_quantity + reserved_quantity)
            quant.write(vals)
        else:
            vals = {
                'product_id': product_id.id,
                'location_id': location_id.id,
                'lot_id': lot_id and lot_id.id,
                'package_id': package_id and package_id.id,
                'owner_id': owner_id and owner_id.id,
                'in_date': in_date,
            }
            if quantity:
                vals['quantity'] = quantity
            if reserved_quantity:
                vals['reserved_quantity'] = reserved_quantity
            self.create(vals)
        return self._get_available_quantity(product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=True, allow_negative=True), in_date