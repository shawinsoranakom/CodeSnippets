def _cart_find_product_line(
        self, product_id, uom_id, linked_line_id=False, no_variant_attribute_value_ids=None, **kwargs
    ):
        """Find the cart line matching the given parameters.

        Custom attributes won't be matched (but no_variant & dynamic ones will be)

        :param int product_id: the product being added/removed, as a `product.product` id
        :param int linked_line_id: optional, the parent line (for optional products), as a
            `sale.order.line` id
        :param list optional_product_ids: optional, the optional products of the line, as a list
            of `product.product` ids
        :param list no_variant_attribute_value_ids: list of `product.template.attribute.value` ids
            whose attribute is configured as `no_variant`
        :param dict kwargs: unused parameters, maybe used in overrides or other cart update methods
        :return: matching order lines in the cart, if any
        :rtype: `sale.order.line` recordset
        """
        self.ensure_one()

        if not self.order_line:
            return self.env['sale.order.line']

        product = self.env['product.product'].browse(product_id)
        if product.type == 'combo':
            return self.env['sale.order.line']

        domain = [
            ('product_id', '=', product_id),
            ('product_uom_id', '=', uom_id),
            ('product_custom_attribute_value_ids', '=', False),
            ('linked_line_id', '=', linked_line_id),
            ('combo_item_id', '=', False),
        ]

        filtered_sol = self.order_line.filtered_domain(domain)
        if not filtered_sol:
            return self.env['sale.order.line']

        has_configurable_no_variant_attributes = any(
            len(line.value_ids) > 1 or line.attribute_id.display_type == 'multi'
            for line in product.attribute_line_ids
            if line.attribute_id.create_variant == 'no_variant'
        )
        if has_configurable_no_variant_attributes:
            filtered_sol = filtered_sol.filtered(
                lambda sol:
                    sol.product_no_variant_attribute_value_ids.ids == no_variant_attribute_value_ids
            )

        return filtered_sol