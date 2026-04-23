def add_to_cart(
        self,
        product_template_id,
        product_id,
        quantity=1.0,
        uom_id=None,
        product_custom_attribute_values=None,
        no_variant_attribute_value_ids=None,
        linked_products=None,
        **kwargs
    ):
        """ Adds a product to the shopping cart.

        :param int product_template_id: The product to add to cart, as a
            `product.template` id.
        :param int product_id: The product to add to cart, as a
            `product.product` id.
        :param int quantity: The quantity to add to the cart.
        :param list[dict] product_custom_attribute_values: A list of objects representing custom
            attribute values for the product. Each object contains:
            - `custom_product_template_attribute_value_id`: The custom attribute's id;
            - `custom_value`: The custom attribute's value.
        :param dict no_variant_attribute_value_ids: The selected non-stored attribute(s), as a list
            of `product.template.attribute.value` ids.
        :param list linked_products: A list of objects representing additional products linked to
            the product added to the cart. Can be combo item or optional products.
        :param dict kwargs: Optional data. This parameter is not used here.
        :return: The values
        :rtype: dict
        """
        order_sudo = request.cart or request.website._create_cart()
        quantity = int(quantity)  # Do not allow float values in ecommerce by default

        product = request.env['product.product'].browse(product_id).exists()
        if not product or not product._is_add_to_cart_allowed():
            raise UserError(_(
                "The given product does not exist therefore it cannot be added to cart."
            ))

        added_qty_per_line = {}
        values = order_sudo.with_context(skip_cart_verification=True)._cart_add(
            product_id=product_id,
            quantity=quantity,
            uom_id=uom_id,
            product_custom_attribute_values=product_custom_attribute_values,
            no_variant_attribute_value_ids=no_variant_attribute_value_ids,
            **kwargs,
        )
        line_ids = {product_template_id: values['line_id']}
        added_qty_per_line[values['line_id']] = values['added_qty']
        is_combo = product.type == 'combo'
        updated_line = (
            values['line_id']
            and order_sudo.order_line.filtered(lambda line: line.id == values['line_id'])
        ) or order_sudo.env['sale.order.line']

        if linked_products and values['line_id']:
            for product_data in linked_products:
                product_sudo = request.env['product.product'].sudo().browse(
                    product_data['product_id']
                ).exists()
                if product_data['quantity'] and (
                    not product_sudo
                    or (
                        not product_sudo._is_add_to_cart_allowed()
                        # For combos, the validity of the given product will be checked
                        # through the SOline constraints (_check_combo_item_id)
                        and not product_data.get('combo_item_id')
                    )
                ):
                    raise UserError(_(
                        "The given product does not exist therefore it cannot be added to cart."
                    ))

                product_values = order_sudo.with_context(skip_cart_verification=True)._cart_add(
                    product_id=product_data['product_id'],
                    quantity=product_data['quantity'],
                    uom_id=product_data.get('uom_id'),
                    product_custom_attribute_values=product_data['product_custom_attribute_values'],
                    no_variant_attribute_value_ids=[
                        int(value_id) for value_id in product_data['no_variant_attribute_value_ids']
                    ],
                    # Using `line_ids[...]` instead of `line_ids.get(...)` ensures that this throws
                    # if an optional product contains bad data.
                    linked_line_id=line_ids[product_data['parent_product_template_id']],
                    **self._get_additional_cart_update_values(product_data),
                    **kwargs,
                )
                if is_combo and not product_values.get('quantity'):
                    # Early return when one of the combo products if fully unavailable
                    # Delete main combo line (and existing children in cascade)
                    updated_line.unlink()
                    # Return empty notification since cart update is considered as failed
                    return {
                        'cart_quantity': order_sudo.cart_quantity,
                        'notification_info': {
                            'warning': product_values.get('warning', ''),
                        },
                        'quantity': 0,
                        'tracking_info': [],
                    }

                line_ids[product_data['product_template_id']] = product_values['line_id']
                added_qty_per_line[product_values['line_id']] = product_values['added_qty']

        warning = values.pop('warning', '')
        if is_combo and order_sudo._check_combo_quantities(updated_line):
            # If quantities were modified through `_check_combo_quantities`, the added qty per line
            # must be adapted accordingly, and the returned warning should be the final one saved
            # on the combo line.
            added_qty_per_line = {
                line.id: updated_line.product_uom_qty
                for line in (updated_line + updated_line.linked_line_ids)
            }
            warning = updated_line.shop_warning
            values['quantity'] = updated_line.product_uom_qty

        # Recompute delivery prices & other cart stuff (loyalty rewards)
        order_sudo._verify_cart_after_update()

        # The validity of a combo product line can only be checked after creating all of its combo
        # item lines.
        main_product_line = request.env['sale.order.line'].browse(values['line_id'])
        if main_product_line.product_type == 'combo':
            main_product_line._check_validity()

        positive_added_qty_per_line = {
            line_id: qty for line_id, qty in added_qty_per_line.items() if qty > 0
        }

        return {
            'cart_quantity': order_sudo.cart_quantity,
            'notification_info': {
                **self._get_cart_notification_information(
                    order_sudo, positive_added_qty_per_line
                ),
                'warning': warning,
            },
            'quantity': values.pop('quantity', 0),
            'tracking_info': self._get_tracking_information(order_sudo, line_ids.values()),
        }