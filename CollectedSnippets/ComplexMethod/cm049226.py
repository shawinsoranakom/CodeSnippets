def write(self, vals):
        if 'uom_id' in vals:
            products = self.filtered(lambda template: template.uom_id.id != vals['uom_id']).product_variant_ids
            products.with_context(skip_uom_conversion=True)._update_uom(vals['uom_id'])
        res = super(ProductTemplate, self).write(vals)
        if self.env.context.get("create_product_product", True) and 'attribute_line_ids' in vals or (vals.get('active') and len(self.product_variant_ids) == 0):
            self._create_variant_ids()
        if 'active' in vals and not vals.get('active'):
            self.with_context(active_test=False).mapped('product_variant_ids').write({'active': vals.get('active')})
        if 'image_1920' in vals:
            self.env['product.product'].invalidate_model([
                'image_1920',
                'image_1024',
                'image_512',
                'image_256',
                'image_128',
                'can_image_1024_be_zoomed',
            ])
        for product_template in self:
            if "type" in vals and vals.get("type") != "combo":
                product_template.combo_ids = False
        return res