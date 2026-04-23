def _compute_days_to_order(self):
        res = super()._compute_days_to_order()
        # Avoid computing rule_ids in case no manufacture rules.
        if not self.env['stock.rule'].search([('action', '=', 'manufacture')]):
            return res
        # Compute rule_ids only for orderpoint with boms
        orderpoints_with_bom = self.filtered(lambda orderpoint: orderpoint.product_id.variant_bom_ids or orderpoint.product_id.bom_ids)
        for orderpoint in orderpoints_with_bom:
            if 'manufacture' in orderpoint.rule_ids.mapped('action'):
                boms = orderpoint.bom_id or orderpoint.product_id.variant_bom_ids or orderpoint.product_id.bom_ids
                orderpoint.days_to_order = boms and boms[0].days_to_prepare_mo or 0
        return res