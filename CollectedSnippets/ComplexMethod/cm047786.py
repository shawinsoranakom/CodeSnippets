def _compute_product_id(self):
        for production in self:
            bom = production.bom_id
            if bom and (
                not production.product_id or bom.product_tmpl_id != production.product_id.product_tmpl_id
                or bom.product_id and bom.product_id != production.product_id
            ):
                production.product_id = bom.product_id or bom.product_tmpl_id.product_variant_id