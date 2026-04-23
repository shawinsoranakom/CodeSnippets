def write(self, vals):
        for product in self:
            if (('type' in vals and vals['type'] != 'service') or ('landed_cost_ok' in vals and not vals['landed_cost_ok'])) and product.type == 'service' and product.landed_cost_ok:
                if self.env['account.move.line'].search_count([('product_id', 'in', product.product_variant_ids.ids), ('is_landed_costs_line', '=', True)]):
                    raise UserError(_("You cannot change the product type or disable landed cost option because the product is used in an account move line."))
                vals['landed_cost_ok'] = False

        return super().write(vals)