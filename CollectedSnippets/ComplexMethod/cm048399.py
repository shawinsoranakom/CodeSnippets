def write(self, vals):
        if 'company_id' in vals and vals['company_id']:
            products_changing_company = self.filtered(lambda product: product.company_id.id != vals['company_id'])
            if products_changing_company:
                move = self.env['stock.move'].sudo().search([
                    ('product_id', 'in', products_changing_company.product_variant_ids.ids),
                    ('company_id', 'not in', [vals['company_id'], False]),
                ], order=None, limit=1)
                if move:
                    raise UserError(_("This product's company cannot be changed as long as there are stock moves of it belonging to another company."))

                # Forbid changing a product's company when quant(s) exist in another company.
                quant = self.env['stock.quant'].sudo().search([
                    ('product_id', 'in', products_changing_company.product_variant_ids.ids),
                    ('company_id', 'not in', [vals['company_id'], False]),
                    ('quantity', '!=', 0),
                ], order=None, limit=1)
                if quant:
                    raise UserError(_("This product's company cannot be changed as long as there are quantities of it belonging to another company."))

        clean_inventory = False
        templates_to_reset = self.env['product.template']
        if 'is_storable' in vals and any(vals['is_storable'] != prod_tmpl.is_storable and not prod_tmpl.is_storable for prod_tmpl in self):
            clean_inventory = True
            if vals['is_storable']:
                templates_to_reset = self.filtered(lambda tmpl: not tmpl.is_storable)

        res = super().write(vals)
        if clean_inventory:
            self.env['stock.quant'].sudo()._clean_reservations()
            templates_to_reset._reset_inventory()
        return res