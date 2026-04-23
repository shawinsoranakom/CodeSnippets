def _gather(self, product_id, location_id, lot_id=None, package_id=None, owner_id=None, strict=False, qty=0):
        """ if records in self, the records are filtered based on the wanted characteristics passed to this function
            if not, a search is done with all the characteristics passed.
        """
        removal_strategy = self._get_removal_strategy(product_id, location_id)
        domain = self._get_gather_domain(product_id, location_id, lot_id, package_id, owner_id, strict)
        if removal_strategy == 'least_packages' and qty:
            domain = self._run_least_packages_removal_strategy_astar(domain, qty)
        order = self._get_removal_strategy_order(removal_strategy)

        quants_cache = self.env.context.get('quants_cache')
        if quants_cache is not None and strict and removal_strategy != 'least_packages':
            res = self.env['stock.quant']
            if lot_id:
                res |= quants_cache[product_id.id, location_id.id, lot_id.id, package_id.id, owner_id.id]
            res |= quants_cache[product_id.id, location_id.id, False, package_id.id, owner_id.id]
        else:
            res = self.search(domain, order=order)
        if removal_strategy == "closest":
            res = res.sorted(lambda q: (q.location_id.complete_name, -q.id))
        return res.sorted(lambda q: not q.lot_id)