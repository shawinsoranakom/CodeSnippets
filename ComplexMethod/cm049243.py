def write(self, vals):
        values = vals
        if 'ptav_product_variant_ids' in values:
            # Force write on this relation from `product.product` to properly
            # trigger `_compute_combination_indices`.
            raise UserError(_("You cannot update related variants from the values. Please update related values from the variants."))
        pav_in_values = 'product_attribute_value_id' in values
        product_in_values = 'product_tmpl_id' in values
        if pav_in_values or product_in_values:
            for ptav in self:
                if pav_in_values and ptav.product_attribute_value_id.id != values['product_attribute_value_id']:
                    raise UserError(_(
                        "You cannot change the value of the value %(value)s set on product %(product)s.",
                        value=ptav.display_name,
                        product=ptav.product_tmpl_id.display_name,
                    ))
                if product_in_values and ptav.product_tmpl_id.id != values['product_tmpl_id']:
                    raise UserError(_(
                        "You cannot change the product of the value %(value)s set on product %(product)s.",
                        value=ptav.display_name,
                        product=ptav.product_tmpl_id.display_name,
                    ))
        res = super().write(values)
        if 'exclude_for' in values:
            self.product_tmpl_id._create_variant_ids()
        return res