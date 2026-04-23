def _compute_bom_id(self):
        mo_by_company_id = defaultdict(lambda: self.env['mrp.production'])
        for mo in self:
            if not mo.product_id and not mo.bom_id:
                mo.bom_id = False
                continue
            mo_by_company_id[mo.company_id.id] |= mo

        for company_id, productions in mo_by_company_id.items():
            picking_type_id = self.env.context.get('default_picking_type_id')
            picking_type = picking_type_id and self.env['stock.picking.type'].browse(picking_type_id)
            boms_by_product = self.env['mrp.bom'].with_context(active_test=True)._bom_find(productions.product_id, picking_type=picking_type, company_id=company_id, bom_type='normal')
            for production in productions:
                if not production.bom_id or production.bom_id.product_tmpl_id != production.product_tmpl_id or (production.bom_id.product_id and production.bom_id.product_id != production.product_id):
                    bom = boms_by_product[production.product_id]
                    production.bom_id = bom.id or False
                    self.env.add_to_compute(production._fields['picking_type_id'], production)