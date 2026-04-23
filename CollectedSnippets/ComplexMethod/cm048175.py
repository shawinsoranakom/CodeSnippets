def _check_bom_lines(self):
        res = super()._check_bom_lines()
        for bom in self:
            if all(not bl.cost_share for bl in bom.bom_line_ids):
                continue
            if any(bl.cost_share < 0 for bl in bom.bom_line_ids):
                raise UserError(_("Components cost share have to be positive or equals to zero."))
            for product in bom.product_tmpl_id.product_variant_ids:
                total_variant_cost_share = sum(bom.bom_line_ids.filtered(lambda bl: not bl._skip_bom_line(product) and not bl.product_uom_id.is_zero(bl.product_qty)).mapped('cost_share'))
                if float_round(total_variant_cost_share, precision_digits=2) not in [0, 100]:
                    raise UserError(_("The total cost share for a BoM's component have to be 100"))
        return res