def _get_cogs_value(self):
        """ Get the COGS price unit in the product's default unit of measure.
        """
        self.ensure_one()

        original_line = self.move_id.reversed_entry_id.line_ids.filtered(
            lambda l: l.display_type == 'cogs' and l.product_id == self.product_id and
            l.product_uom_id == self.product_uom_id and l.price_unit >= 0)
        original_line = original_line and original_line[0]
        if original_line:
            return original_line.price_unit

        if not self.product_id or self.product_uom_id.is_zero(self.quantity):
            return self.price_unit

        cogs_qty = self._get_cogs_qty()
        if moves := self._get_stock_moves().filtered(lambda m: m.state == 'done'):
            price_unit = moves._get_cogs_price_unit(cogs_qty)
        else:
            if self.product_id.cost_method in ['standard', 'average']:
                price_unit = self.product_id.standard_price
            else:
                price_unit = self.product_id._run_fifo(cogs_qty) / cogs_qty if cogs_qty else 0
        line_quantity_uom = self.product_uom_id._compute_quantity(self.quantity, self.product_id.uom_id)
        return (price_unit * cogs_qty - self._get_posted_cogs_value()) / line_quantity_uom