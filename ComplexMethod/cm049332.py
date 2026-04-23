def shop_address_submit(
        self,
        partner_id=None,
        address_type='billing',
        use_delivery_as_billing=None,
        callback=None,
        **form_data
    ):
        """ Create or update an address.

        If it succeeds, it returns the URL to redirect (client-side) to. If it fails (missing or
        invalid information), it highlights the problematic form input with the appropriate error
        message.

        :param str partner_id: The partner whose address to update with the address form, if any.
        :param str address_type: The type of the address: 'billing' or 'delivery'.
        :param str use_delivery_as_billing: Whether the provided address should be used as both the
                                            billing and the delivery address. 'true' or 'false'.
        :param str callback: The URL to redirect to in case of successful address creation/update.
        :param dict form_data: The form data to process as address values.
        :return: A JSON-encoded feedback, with either the success URL or an error message.
        :rtype: str
        """
        order_sudo = request.cart
        if redirection := self._check_cart(order_sudo):
            return json.dumps({'redirectUrl': redirection.location})

        # Retrieve the partner whose address to update, if any, and its address type.
        partner_sudo, address_type = self._prepare_address_update(
            order_sudo, partner_id=partner_id and int(partner_id), address_type=address_type
        )

        is_new_address = not partner_sudo
        if is_new_address or order_sudo.only_services:
            callback = callback or '/shop/checkout?try_skip_step=true'
        else:
            callback = callback or '/shop/checkout'

        partner_sudo, feedback_dict = self._create_or_update_address(
            partner_sudo,
            address_type=address_type,
            use_delivery_as_billing=use_delivery_as_billing,
            callback=callback,
            order_sudo=order_sudo,
            **form_data
        )

        if feedback_dict.get('invalid_fields'):
            return json.dumps(feedback_dict) # Return if error when creating/updating partner.

        is_anonymous_cart = order_sudo._is_anonymous_cart()
        is_main_address = is_anonymous_cart or order_sudo.partner_id.id == partner_sudo.id
        partner_fnames = set()
        if is_main_address:  # Main customer address updated.
            partner_fnames.add('partner_id')  # Force the re-computation of partner-based fields.

        if address_type == 'billing':
            partner_fnames.add('partner_invoice_id')
            if is_new_address and order_sudo.only_services:
                # The delivery address is required to make the order.
                partner_fnames.add('partner_shipping_id')
        elif address_type == 'delivery':
            partner_fnames.add('partner_shipping_id')
            if use_delivery_as_billing:
                partner_fnames.add('partner_invoice_id')

        order_sudo._update_address(partner_sudo.id, partner_fnames)

        if order_sudo._is_anonymous_cart():
            # Unsubscribe the public partner if the cart was previously anonymous.
            order_sudo.message_unsubscribe(order_sudo.website_id.partner_id.ids)

        return json.dumps(feedback_dict)