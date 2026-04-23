def _get_products_and_taxes_dict(self, line, products, taxes, currency):
        key2 = (line.product_id, line.price_unit, line.discount)
        key1 = line.product_id.product_tmpl_id.pos_categ_ids[0].name if len(line.product_id.product_tmpl_id.pos_categ_ids) else _('Not Categorized')
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        products.setdefault(key1, {})
        products[key1].setdefault(key2, [0.0, 0.0, 0.0, ''])
        products[key1][key2][0] = round(products[key1][key2][0] + abs(line.qty), precision)
        products[key1][key2][1] += self._get_product_total_amount(line)
        products[key1][key2][2] += line.price_subtotal

        # Name of each combo products along with the combo
        if line.combo_line_ids:
            combo_products_label = ' (' + ", ".join(line.combo_line_ids.product_id.mapped('name')) + ')'
            products[key1][key2][3] = combo_products_label

        if line.tax_ids_after_fiscal_position:
            line_taxes = line.tax_ids_after_fiscal_position.sudo().compute_all(line.price_unit * (1-(line.discount or 0.0)/100.0), currency, line.qty, product=line.product_id, partner=line.order_id.partner_id or False)
            base_amounts = {}
            for tax in line_taxes['taxes']:
                taxes['taxes'].setdefault(tax['id'], {'name': tax['name'], 'tax_amount': 0.0, 'base_amount': 0.0})
                taxes['taxes'][tax['id']]['tax_amount'] += tax['amount']
                base_amounts[tax['id']] = tax['base']

            for tax_id, base_amount in base_amounts.items():
                taxes['taxes'][tax_id]['base_amount'] += currency.round(base_amount)
        else:
            taxes['taxes'].setdefault(0, {'name': _('No Taxes'), 'tax_amount': 0.0, 'base_amount': 0.0})
            taxes['taxes'][0]['base_amount'] += line.price_subtotal_incl

        refund_sign = -1 if line.order_id.is_refund else 1
        taxes['base_amount'] += line.price_subtotal * refund_sign
        return products, taxes