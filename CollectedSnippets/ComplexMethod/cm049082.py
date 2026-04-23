def _get_cogs_price_unit(self, quantity=0):
        """ Returns the COGS unit price to value this stock move
        quantity should be given in product uom """

        if len(self.product_id) > 1:
            return 0
        total_qty = sum(m._get_valued_qty() for m in self)
        valued_consigned_qty = self._get_valued_consigned_qty()
        total_valued_qty = total_qty + valued_consigned_qty
        if total_valued_qty and (self.product_id.cost_method == 'fifo' or valued_consigned_qty or
            (self.product_id.lot_valuated and self.product_id.cost_method == 'average')):
            return sum(self.mapped('value')) / total_valued_qty
        else:
            return self.product_id.standard_price