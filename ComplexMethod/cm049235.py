def _compute_name(self):
        for item in self:
            if item.categ_id and item.applied_on == '2_product_category':
                item.name = _("Category: %s", item.categ_id.display_name)
            elif item.product_tmpl_id and item.applied_on == '1_product':
                item.name = item.product_tmpl_id.display_name
            elif item.product_id and item.applied_on == '0_product_variant':
                item.name = _("Variant: %s", item.product_id.display_name)
            elif item.display_applied_on == '2_product_category':
                item.name = _("All Categories")
            else:
                item.name = _("All Products")