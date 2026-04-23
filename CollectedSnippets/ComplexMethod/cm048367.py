def _search_product_qty(self, operator, value):
        op = PY_OPERATORS.get(operator)
        if not op:
            return NotImplemented
        if isinstance(value, Iterable) and not isinstance(value, str):
            value = {float(v) for v in value}
        else:
            value = float(value)
        domain = [
            ('lot_id', '!=', False),
            '|', ('location_id.usage', '=', 'internal'),
            '&', ('location_id.usage', '=', 'transit'), ('location_id.company_id', 'in', self.env.companies.ids)
        ]
        lots_w_qty = self.env['stock.quant']._read_group(domain=domain, groupby=['lot_id'], aggregates=['quantity:sum'], having=[('quantity:sum', '!=', 0)])
        ids = []
        lot_ids_w_qty = []
        for lot, quantity_sum in lots_w_qty:
            lot_id = lot.id
            lot_ids_w_qty.append(lot_id)
            if op(quantity_sum, value):
                ids.append(lot_id)

        # check if we need include zero values in result
        include_zero = op(0.0, value)
        if include_zero:
            return ['|', ('id', 'in', ids), ('id', 'not in', lot_ids_w_qty)]
        return [('id', 'in', ids)]