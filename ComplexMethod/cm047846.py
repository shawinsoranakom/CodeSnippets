def _run_manufacture(self, procurements):
        new_productions_values_by_company = defaultdict(lambda: defaultdict(list))
        for procurement, rule in procurements:
            if procurement.product_uom.compare(procurement.product_qty, 0) <= 0:
                # If procurement contains negative quantity, don't create a MO that would be for a negative value.
                continue
            bom = rule._get_matching_bom(procurement.product_id, procurement.company_id, procurement.values)

            mo = self.env['mrp.production']
            if procurement.origin != 'MPS':
                domain = rule._make_mo_get_domain(procurement, bom)
                mo = self.env['mrp.production'].sudo().search(domain, limit=1)
            is_batch_size = bom and bom.enable_batch_size
            if not mo or is_batch_size:
                procurement_qty = procurement.product_qty
                batch_size = bom.product_uom_id._compute_quantity(bom.batch_size, procurement.product_uom) if is_batch_size else procurement_qty
                vals = rule._prepare_mo_vals(*procurement, bom)
                while procurement.product_uom.compare(procurement_qty, 0) > 0:
                    new_productions_values_by_company[procurement.company_id.id]['values'].append({
                        **vals,
                        'product_qty': procurement.product_uom._compute_quantity(batch_size, bom.product_uom_id) if bom else procurement_qty,
                    })
                    new_productions_values_by_company[procurement.company_id.id]['procurements'].append(procurement)
                    procurement_qty -= batch_size
            else:
                procurement_product_uom_qty = procurement.product_uom._compute_quantity(procurement.product_qty, procurement.product_id.uom_id)
                self.env['change.production.qty'].sudo().with_context(skip_activity=True).create({
                    'mo_id': mo.id,
                    'product_qty': mo.product_id.uom_id._compute_quantity((mo.product_uom_qty + procurement_product_uom_qty), mo.product_uom_id),
                }).change_prod_qty()

        for company_id in new_productions_values_by_company:
            productions_vals_list = new_productions_values_by_company[company_id]['values']
            # create the MO as SUPERUSER because the current user may not have the rights to do it (mto product launched by a sale for example)
            productions = self.env['mrp.production'].with_user(SUPERUSER_ID).sudo().with_company(company_id).create(productions_vals_list)
            for mo in productions:
                if self._should_auto_confirm_procurement_mo(mo):
                    mo.action_confirm()
            productions._post_run_manufacture(new_productions_values_by_company[company_id]['procurements'])
        return True