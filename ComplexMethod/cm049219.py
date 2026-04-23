def unlink(self):
        if self.env.context.get('create_product_product') is False:
            return super().unlink()

        unlink_products_ids = set()
        unlink_templates_ids = set()

        # Check if products still exists, in case they've been unlinked by unlinking their template
        existing_products = self.exists()
        product_ids_by_template_id = {template.id: set(ids) for template, ids in self.with_context(active_test=False)._read_group(
            domain=[('product_tmpl_id', 'in', existing_products.product_tmpl_id.ids)],
            groupby=['product_tmpl_id'],
            aggregates=['id:array_agg'],
        )}
        for product in existing_products:
            # If there is an image set on the variant and no image set on the
            # template, move the image to the template.
            if product.image_variant_1920 and not product.product_tmpl_id.image_1920:
                product.product_tmpl_id.image_1920 = product.image_variant_1920
            # Check if the product is last product of this template...
            has_other_products = product_ids_by_template_id.get(product.product_tmpl_id.id, set()) - {product.id}
            # ... and do not delete product template if it's configured to be created "on demand"
            if not has_other_products and not product.product_tmpl_id.has_dynamic_attributes():
                unlink_templates_ids.add(product.product_tmpl_id.id)
            unlink_products_ids.add(product.id)
        unlink_products = self.env['product.product'].browse(unlink_products_ids)
        res = super(ProductProduct, unlink_products).unlink()
        # delete templates after calling super, as deleting template could lead to deleting
        # products due to ondelete='cascade'
        unlink_templates = self.env['product.template'].browse(unlink_templates_ids)
        unlink_templates.unlink()
        # `_get_variant_id_for_combination` depends on existing variants
        self.env.registry.clear_cache()
        return res