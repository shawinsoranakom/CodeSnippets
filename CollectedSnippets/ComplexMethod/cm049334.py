def process_express_checkout(
        self, billing_address, shipping_address=None, shipping_option=None, **kwargs
    ):
        """ Records the partner information on the order when using express checkout flow.

        Depending on whether the partner is registered and logged in, either creates a new partner
        or uses an existing one that matches all received data.

        :param dict billing_address: Billing information sent by the express payment form.
        :param dict shipping_address: Shipping information sent by the express payment form.
        :param dict shipping_option: Carrier information sent by the express payment form.
        :param dict kwargs: Optional data. This parameter is not used here.
        :return int: The order's partner id.
        """
        order_sudo = request.cart

        # Update the partner with all the information
        self._include_country_and_state_in_address(billing_address)
        billing_address, _side_values = self._parse_form_data(billing_address)
        if order_sudo._is_anonymous_cart():

            # Pricelist are recomputed every time the partner is changed. We don't want to recompute
            # the price with another pricelist at this state since the customer has already accepted
            # the amount and validated the payment.
            new_partner_sudo = self._create_new_address(
                billing_address,
                address_type='billing',
                use_delivery_as_billing=False,
                order_sudo=order_sudo,
            )
            with request.env.protecting([order_sudo._fields['pricelist_id']], order_sudo):
                order_sudo.partner_id = new_partner_sudo
        elif not self._are_same_addresses(billing_address, order_sudo.partner_invoice_id):
            # Check if a child partner doesn't already exist with the same informations. The
            # phone isn't always checked because it isn't sent in shipping information with
            # Google Pay.
            child_partner_id = self._find_child_partner(
                order_sudo.partner_id.commercial_partner_id.id, billing_address
            )
            order_sudo.partner_invoice_id = child_partner_id or self._create_new_address(
                billing_address,
                address_type='billing',
                use_delivery_as_billing=False,
                order_sudo=order_sudo,
            )

        # In a non-express flow, `sale_last_order_id` would be added in the session before the
        # payment. As we skip all the steps with the express checkout, `sale_last_order_id` must be
        # assigned to ensure the right behavior from `shop_payment_confirmation()`.
        request.session['sale_last_order_id'] = order_sudo.id

        if shipping_address:
            #in order to not override shippig address, it's checked separately from shipping option
            self._include_country_and_state_in_address(shipping_address)
            shipping_address, _side_values = self._parse_form_data(shipping_address)

            if order_sudo.name in order_sudo.partner_shipping_id.name:
                # The existing partner was created by `process_express_checkout_delivery_choice`, it
                # means that the partner is missing information, so we update it.
                order_sudo.partner_shipping_id.write(shipping_address)
                order_sudo._update_address(
                    order_sudo.partner_shipping_id.id, ['partner_shipping_id']
                )
            elif not self._are_same_addresses(shipping_address, order_sudo.partner_shipping_id):
                # The sale order's shipping partner's address is different from the one received. If
                # all the sale order's child partners' address differs from the one received, we
                # create a new partner. The phone isn't always checked because it isn't sent in
                # shipping information with Google Pay.
                child_partner_id = self._find_child_partner(
                    order_sudo.partner_id.commercial_partner_id.id, shipping_address
                )
                order_sudo.partner_shipping_id = child_partner_id or self._create_new_address(
                    shipping_address,
                    address_type='delivery',
                    use_delivery_as_billing=False,
                    order_sudo=order_sudo,
                )
            # Process the delivery method.
            if shipping_option:
                dm_id = int(shipping_option['id'])
                available_dms = order_sudo._get_delivery_methods()
                order_sudo._set_delivery_method(available_dms.filtered(lambda dm: dm.id == dm_id))

        return order_sudo.partner_id.id