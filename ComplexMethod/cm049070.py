def _change_standard_price(self, old_price):
        product_values = []
        product_ids_lot_valuated = set()
        date = self.env.context.get('valuation_date') or fields.Datetime.now()
        for product in self:
            if product.cost_method == 'fifo' or product.standard_price == old_price.get(product):
                continue

            if product.lot_valuated:
                product_ids_lot_valuated.add(product.id)

            product_values.append({
                'product_id': product.id,
                'value': product.standard_price,
                'company_id': product.company_id.id or self.env.company.id,
                'date': date,
                'description': _('Price update from %(old_price)s to %(new_price)s by %(user)s',
                    old_price=old_price.get(product), new_price=product.standard_price, user=self.env.user.name)
            })
        self.env['product.value'].sudo().create(product_values)
        if product_ids_lot_valuated:
            for (product, lots) in self.env['stock.lot']._read_group(
                    [('product_id', 'in', product_ids_lot_valuated)], ['product_id'], ['id:recordset']):
                lots.with_context(disable_auto_revaluation=True).standard_price = product.standard_price
        return