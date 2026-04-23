def _prepare_order_line_values(
        self,
        product_id,
        quantity,
        uom_id,
        *,
        linked_line_id=False,
        no_variant_attribute_value_ids=None,
        product_custom_attribute_values=None,
        combo_item_id=None,
        **kwargs
    ):
        self.ensure_one()
        product = self.env['product.product'].browse(product_id)

        no_variant_attribute_values = product.env['product.template.attribute.value'].browse(
            no_variant_attribute_value_ids
        )
        received_combination = product.product_template_attribute_value_ids | no_variant_attribute_values
        product_template = product.product_tmpl_id

        # handle all cases where incorrect or incomplete data are received
        combination = product_template._get_closest_possible_combination(received_combination)

        # get or create (if dynamic) the correct variant
        product = product_template._create_product_variant(combination)

        if not product:
            raise UserError(_("The given combination does not exist therefore it cannot be added to cart."))

        if linked_line_id and linked_line_id not in self.order_line.ids:
            # Make sure the provided parent line belongs to the current order.
            raise UserError(_("Invalid request parameters."))

        values = {
            'product_id': product.id,
            'product_uom_qty': quantity,
            'product_uom_id': uom_id or product.uom_id.id,
            'order_id': self.id,
            'linked_line_id': linked_line_id,
            'combo_item_id': combo_item_id,
        }

        # add no_variant attributes that were not received
        no_variant_attribute_values |= combination.filtered(
            lambda ptav: ptav.attribute_id.create_variant == 'no_variant'
        )

        if no_variant_attribute_values:
            values['product_no_variant_attribute_value_ids'] = [Command.set(no_variant_attribute_values.ids)]

        # add is_custom attribute values that were not received
        custom_values = product_custom_attribute_values or []
        received_custom_values = product.env['product.template.attribute.value'].browse([
            int(ptav['custom_product_template_attribute_value_id'])
            for ptav in custom_values
        ])

        for ptav in combination.filtered(lambda ptav: ptav.is_custom and ptav not in received_custom_values):
            custom_values.append({
                'custom_product_template_attribute_value_id': ptav.id,
                'custom_value': '',
            })

        if custom_values:
            values['product_custom_attribute_value_ids'] = [
                fields.Command.create({
                    'custom_product_template_attribute_value_id': custom_value['custom_product_template_attribute_value_id'],
                    'custom_value': custom_value['custom_value'],
                }) for custom_value in custom_values
            ]

        return values