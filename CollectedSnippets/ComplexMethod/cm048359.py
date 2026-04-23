def default_get(self, fields):
        res = super(ProductReplenish, self).default_get(fields)
        product_tmpl_id = self.env['product.template']
        if self.env.context.get('default_product_id'):
            product_id = self.env['product.product'].browse(self.env.context['default_product_id'])
            product_tmpl_id = product_id.product_tmpl_id
            if 'product_id' in fields:
                res['product_tmpl_id'] = product_id.product_tmpl_id.id
                res['product_id'] = product_id.id
        elif self.env.context.get('default_product_tmpl_id'):
            product_tmpl_id = self.env['product.template'].browse(self.env.context['default_product_tmpl_id'])
            if 'product_id' in fields:
                res['product_tmpl_id'] = product_tmpl_id.id
                res['product_id'] = product_tmpl_id.product_variant_id.id
                if len(product_tmpl_id.product_variant_ids) > 1:
                    res['product_has_variants'] = True
        company = product_tmpl_id.company_id or self.env.company
        if 'product_uom_id' in fields:
            res['product_uom_id'] = product_tmpl_id.uom_id.id
        if 'company_id' in fields:
            res['company_id'] = company.id
        if 'warehouse_id' in fields and 'warehouse_id' not in res:
            warehouse = self.env['stock.warehouse'].search([('company_id', '=', company.id)], limit=1)
            res['warehouse_id'] = warehouse.id
        if 'route_id' in fields and 'route_id' not in res and product_tmpl_id:
            res['route_id'] = self.env['stock.route'].search(self._get_route_domain(product_tmpl_id), limit=1).id
            if not res['route_id']:
                if product_tmpl_id.route_ids:
                    res['route_id'] = product_tmpl_id.route_ids.filtered(lambda r: r.company_id == self.env.company or not r.company_id)[0].id
        return res