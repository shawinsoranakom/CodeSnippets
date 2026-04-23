def default_get(self, fields):
        res = super(StockRulesReport, self).default_get(fields)
        product_tmpl_id = self.env['product.template']
        if 'product_id' in fields:
            if self.env.context.get('default_product_id'):
                product_id = self.env['product.product'].browse(self.env.context['default_product_id'])
                product_tmpl_id = product_id.product_tmpl_id
                res['product_tmpl_id'] = product_id.product_tmpl_id.id
                res['product_id'] = product_id.id
            elif self.env.context.get('default_product_tmpl_id'):
                product_tmpl_id = self.env['product.template'].browse(self.env.context['default_product_tmpl_id'])
                res['product_tmpl_id'] = product_tmpl_id.id
                res['product_id'] = product_tmpl_id.product_variant_id.id
                if len(product_tmpl_id.product_variant_ids) > 1:
                    res['product_has_variants'] = True
        if 'warehouse_ids' in fields:
            company = product_tmpl_id.company_id or self.env.company
            warehouse_id = self.env['stock.warehouse'].search(self.env['stock.warehouse']._check_company_domain(company), limit=1).id
            if not warehouse_id:
                self.env['stock.warehouse']._warehouse_redirect_warning()
            res['warehouse_ids'] = [(6, 0, [warehouse_id])]
        return res