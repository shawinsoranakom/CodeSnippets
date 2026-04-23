def onchange_product_tmpl_id(self):
        if self.product_tmpl_id:
            warning = (
                self.bom_line_ids.bom_product_template_attribute_value_ids or
                self.operation_ids.bom_product_template_attribute_value_ids or
                self.byproduct_ids.bom_product_template_attribute_value_ids
            ) and {
                'warning': {
                    'title': _("Warning"),
                    'message': _("Changing the product or variant will permanently reset all previously encoded variant-related data."),
                }
            }
            default_uom_id = self.env.context.get('default_product_uom_id')
            # Avoids updating the BoM's UoM in case a specific UoM was passed through as a default value.
            if self.product_uom_id.id != default_uom_id:
                self.product_uom_id = self.product_tmpl_id.uom_id.id
            if self.product_id.product_tmpl_id != self.product_tmpl_id:
                self.product_id = False
            self.bom_line_ids.bom_product_template_attribute_value_ids = False
            self.operation_ids.bom_product_template_attribute_value_ids = False
            self.byproduct_ids.bom_product_template_attribute_value_ids = False

            domain = [('product_tmpl_id', '=', self.product_tmpl_id.id)]
            if self.id.origin:
                domain.append(('id', '!=', self.id.origin))
            number_of_bom_of_this_product = self.env['mrp.bom'].search_count(domain)
            if number_of_bom_of_this_product:  # add a reference to the bom if there is already a bom for this product
                self.code = _("%(product_name)s (new) %(number_of_boms)s", product_name=self.product_tmpl_id.name, number_of_boms=number_of_bom_of_this_product)
            if warning:
                return warning