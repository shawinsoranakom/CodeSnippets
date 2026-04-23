def _get_value_from_account_move(self, quantity, at_date=None):
        valuation_data = super()._get_value_from_account_move(quantity, at_date=at_date)
        if not self.purchase_line_id:
            return valuation_data

        if isinstance(at_date, datetime):
            # Since aml.date are Date, we don't need the extra precision here.
            at_date = Date.to_date(at_date)

        aml_quantity = 0
        value = 0
        aml_ids = set()
        for aml in self.purchase_line_id.invoice_lines:
            if at_date and aml.date > at_date:
                continue
            if aml.move_id.state != 'posted':
                continue
            aml_ids.add(aml.id)
            if aml.move_type == 'in_invoice':
                aml_quantity += self._get_quantity_from_bill(aml, quantity)
                value += self._get_value_from_bill(aml)
            elif aml.move_type == 'in_refund':
                aml_quantity -= self._get_quantity_from_bill(aml, quantity)
                value -= self._get_value_from_bill(aml)

        if aml_quantity <= 0:
            return valuation_data

        other_candidates_qty = 0
        for move in self.purchase_line_id.move_ids:
            if move == self:
                continue
            if move.product_id != self.product_id:
                continue
            if move.date > self.date or (move.date == self.date and move.id > self.id):
                continue
            if move.is_in or move.is_dropship:
                other_candidates_qty += move._get_valued_qty()
            elif move.is_out:
                other_candidates_qty -= -move._get_valued_qty()

        if self.product_uom.compare(aml_quantity, other_candidates_qty) <= 0:
            return valuation_data

        # Remove quantity from prior moves.
        value = value * ((aml_quantity - other_candidates_qty) / aml_quantity)
        aml_quantity = aml_quantity - other_candidates_qty

        if quantity >= aml_quantity:
            valuation_data['quantity'] = aml_quantity
            valuation_data['value'] = value
        else:
            valuation_data['quantity'] = quantity
            valuation_data['value'] = quantity * value / aml_quantity
        account_moves = self.env['account.move.line'].browse(aml_ids).move_id
        valuation_data['description'] = self.env._('%(value)s for %(quantity)s %(unit)s from %(bills)s',
            value=self.company_currency_id.format(value), quantity=aml_quantity, unit=self.product_id.uom_id.name,
            bills=account_moves.mapped('display_name'))
        return valuation_data