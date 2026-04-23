def _update_product_template_attribute_values(self):
        """Create or unlink `product.template.attribute.value` for each line in
        `self` based on `value_ids`.

        The goal is to delete all values that are not in `value_ids`, to
        activate those in `value_ids` that are currently archived, and to create
        those in `value_ids` that didn't exist.

        This is a trick for the form view and for performance in general,
        because we don't want to generate in advance all possible values for all
        templates, but only those that will be selected.
        """
        ProductTemplateAttributeValue = self.env['product.template.attribute.value']
        ptav_to_create = []
        ptav_to_unlink = ProductTemplateAttributeValue
        for ptal in self:
            ptav_to_activate = ProductTemplateAttributeValue
            remaining_pav = set(ptal.value_ids.ids)
            for ptav in ptal.product_template_value_ids:
                if ptav.product_attribute_value_id.id not in remaining_pav:
                    # Remove values that existed but don't exist anymore, but
                    # ignore those that are already archived because if they are
                    # archived it means they could not be deleted previously.
                    if ptav.ptav_active:
                        ptav_to_unlink += ptav
                else:
                    # Activate corresponding values that are currently archived.
                    remaining_pav.remove(ptav.product_attribute_value_id.id)
                    if not ptav.ptav_active:
                        ptav_to_activate += ptav

            ptav_groups = ProductTemplateAttributeValue._read_group([
                    ('ptav_active', '=', False),
                    ('product_tmpl_id', '=', ptal.product_tmpl_id.id),
                    ('attribute_id', '=', ptal.attribute_id.id),
                    ('product_attribute_value_id', 'in', list(remaining_pav)),
                ], groupby=["product_attribute_value_id"], aggregates=["id:recordset"])

            for pav, ptav in ptav_groups:
                ptav = ptav[0]
                ptav.write({'ptav_active': True, 'attribute_line_id': ptal.id})
                # If the value was marked for deletion, now keep it.
                ptav_to_unlink -= ptav
                remaining_pav.remove(pav.id)

            remaining_pav = self.env['product.attribute.value'].sudo().browse(sorted(remaining_pav))

            for pav in remaining_pav:
                ptav_to_create.append({
                    'product_attribute_value_id': pav.id,
                    'attribute_line_id': ptal.id,
                    'price_extra': pav.default_extra_price,
                })
            # Handle active at each step in case a following line might want to
            # re-use a value that was archived at a previous step.
            ptav_to_activate.write({'ptav_active': True})
            ptav_to_unlink.write({'ptav_active': False})
        if ptav_to_unlink:
            ptav_to_unlink.unlink()
        ProductTemplateAttributeValue.create(ptav_to_create)
        if self.env.context.get('create_product_product', True):
            self.product_tmpl_id._create_variant_ids()