def write(self, vals):
        product_ids_to_update = set()
        lot_ids_to_update = set()
        if 'categ_id' in vals:
            category = self.env['product.category'].browse(vals['categ_id'])
            cost_method = category.property_cost_method if category else self.env.company.cost_method
            for product in self:
                if product.cost_method != cost_method:
                    product_ids_to_update.update(product.product_variant_ids.ids)

        if 'lot_valuated' in vals:
            if vals.get('lot_valuated'):
                products_to_enable = self.filtered(lambda p: not p.lot_valuated)
                if products_to_enable:
                    problematic_quants = self.env['stock.quant'].search([
                        ('product_id', 'in', products_to_enable.product_variant_ids.ids),
                        ('lot_id', '=', False),
                        ('quantity', '!=', 0),
                        ('location_id.is_valued_internal', '=', True),
                    ])
                    if problematic_quants:
                        raise UserError(self.env._(
                            "You cannot enable lot valuation because the following products have"
                            " on-hand quantities without a lot/serial number:\n%s",
                            problematic_quants.product_id.mapped('display_name'),
                        ))
            for product in self:
                if product.lot_valuated != vals.get('lot_valuated', product.lot_valuated):
                    product_ids_to_update.update(product.product_variant_ids.ids)

        products_to_update = self.env['product.product'].browse(product_ids_to_update)
        lot_ids_to_update.update(self.env['stock.lot'].sudo().search([
            ('product_id', 'in', products_to_update.filtered(lambda p: p.lot_valuated).ids),
        ]).ids)

        res = super().write(vals)
        if 'lot_valuated' in vals:
            lot_ids_to_update.update(self.env['stock.lot'].sudo().search([
                ('product_id', 'in', self.product_variant_ids.ids),
            ]).ids)
        if product_ids_to_update:
            self.env['product.product'].browse(product_ids_to_update)._update_standard_price()
        if lot_ids_to_update:
            self.env['stock.lot'].browse(lot_ids_to_update).sudo()._update_standard_price()
        return res