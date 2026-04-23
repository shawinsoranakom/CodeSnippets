def _check_bom_lines(self):
        for bom in self:
            apply_variants = bom.bom_line_ids.bom_product_template_attribute_value_ids | bom.operation_ids.bom_product_template_attribute_value_ids | bom.byproduct_ids.bom_product_template_attribute_value_ids
            if bom.product_id and apply_variants:
                raise ValidationError(_("You cannot use the 'Apply on Variant' functionality and simultaneously create a BoM for a specific variant."))
            for ptav in apply_variants:
                if ptav.product_tmpl_id != bom.product_tmpl_id:
                    raise ValidationError(_(
                        "The attribute value %(attribute)s set on product %(product)s does not match the BoM product %(bom_product)s.",
                        attribute=ptav.display_name,
                        product=ptav.product_tmpl_id.display_name,
                        bom_product=bom.product_tmpl_id.display_name
                    ))
            for byproduct in bom.byproduct_ids:
                if bom.product_id:
                    same_product = bom.product_id == byproduct.product_id
                else:
                    same_product = bom.product_tmpl_id == byproduct.product_id.product_tmpl_id
                if same_product:
                    raise ValidationError(_("By-product %s should not be the same as BoM product.", bom.display_name))
                if byproduct.cost_share < 0:
                    raise ValidationError(_("By-products cost shares must be positive."))
            for product in bom.product_tmpl_id.product_variant_ids:
                total_variant_cost_share = sum(bom.byproduct_ids.filtered(lambda bp: not bp._skip_byproduct_line(product) and not bp.product_uom_id.is_zero(bp.product_qty)).mapped('cost_share'))
                if float_compare(total_variant_cost_share, 100, precision_digits=2) > 0:
                    raise ValidationError(_("The total cost share for a BoM's by-products cannot exceed 100."))