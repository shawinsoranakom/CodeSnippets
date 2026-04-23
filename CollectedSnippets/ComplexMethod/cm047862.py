def _get_byproducts_lines(self, product, bom, bom_quantity, level, total, index):
        byproducts = []
        byproduct_cost_portion = 0
        company = bom.company_id or self.env.company
        byproduct_index = 0
        for byproduct in bom.byproduct_ids:
            if byproduct._skip_byproduct_line(product):
                continue
            line_quantity = (bom_quantity / (bom.product_qty or 1.0)) * byproduct.product_qty
            cost_share = byproduct.cost_share / 100 if byproduct.product_qty > 0 else 0
            byproduct_cost_portion += cost_share
            price = byproduct.product_id.uom_id._compute_price(byproduct.product_id.with_company(company).standard_price, byproduct.product_uom_id) * line_quantity
            byproducts.append({
                'id': byproduct.id,
                'index': f"{index}{byproduct_index}",
                'type': 'byproduct',
                'link_id': byproduct.product_id.id if byproduct.product_id.product_variant_count > 1 else byproduct.product_id.product_tmpl_id.id,
                'link_model': 'product.product' if byproduct.product_id.product_variant_count > 1 else 'product.template',
                'currency_id': company.currency_id.id,
                'name': byproduct.product_id.display_name,
                'quantity': line_quantity,
                'uom_name': byproduct.product_uom_id.name,
                'parent_id': bom.id,
                'level': level or 0,
                'bom_cost': company.currency_id.round(total * cost_share),
                'cost_share': cost_share,
            })
            byproduct_index += 1
        return byproducts, byproduct_cost_portion