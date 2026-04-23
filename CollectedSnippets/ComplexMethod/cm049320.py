def express_checkout_process_delivery_address(self, partial_delivery_address):
        """ Process the shipping address and return the available delivery methods.

        Depending on whether the partner is registered and logged in, a new partner is created or we
        use an existing partner that matches the partial delivery address received.

        :param dict partial_delivery_address: The delivery information sent by the express payment
                                              provider.
        :return: The available delivery methods, sorted by lowest price.
        :rtype: dict
        """
        if not (order_sudo := request.cart):
            return []

        self._include_country_and_state_in_address(partial_delivery_address)
        partial_delivery_address, _side_values = self._parse_form_data(partial_delivery_address)
        if order_sudo._is_anonymous_cart():
            # The partner_shipping_id and partner_invoice_id will be automatically computed when
            # changing the partner_id of the SO. This allows website_sale to avoid creating
            # duplicates.
            partial_delivery_address['name'] = _(
                'Anonymous express checkout partner for order %s',
                order_sudo.name,
            )
            new_partner_sudo = self._create_new_address(
                address_values=partial_delivery_address,
                address_type='delivery',
                use_delivery_as_billing=False,
                order_sudo=order_sudo,
            )
            # Pricelists are recomputed every time the partner is changed. We don't want to
            # recompute the price with another pricelist at this state since the customer has
            # already accepted the amount and validated the payment.
            with request.env.protecting([order_sudo._fields['pricelist_id']], order_sudo):
                order_sudo.partner_id = new_partner_sudo
        elif order_sudo.name in order_sudo.partner_shipping_id.name:
            order_sudo.partner_shipping_id.write(partial_delivery_address)
            # TODO VFE TODO VCR do we want to trigger cart recomputation here ?
            # order_sudo._update_address(
            #     order_sudo.partner_shipping_id.id, ['partner_shipping_id']
            # )
        elif not self._are_same_addresses(
            partial_delivery_address,
            order_sudo.partner_shipping_id,
        ):
            # Check if a child partner doesn't already exist with the same information. The phone
            # isn't always checked because it isn't sent in delivery information with Google Pay.
            child_partner_id = self._find_child_partner(
                order_sudo.partner_id.commercial_partner_id.id, partial_delivery_address
            )
            partial_delivery_address['name'] = _(
                'Anonymous express checkout partner for order %s',
                order_sudo.name,
            )
            order_sudo.partner_shipping_id = child_partner_id or self._create_new_address(
                address_values=partial_delivery_address,
                address_type='delivery',
                use_delivery_as_billing=False,
                order_sudo=order_sudo,
            )

        sorted_delivery_methods = sorted([{
            'id': dm.id,
            'name': dm.name,
            'description': dm.website_description,
            'minorAmount': payment_utils.to_minor_currency_units(price, order_sudo.currency_id),
        } for dm, price in self._get_delivery_methods_express_checkout(order_sudo).items()
        ], key=lambda dm: dm['minorAmount'])

        # Preselect the cheapest method imitating the behavior of the express checkout form.
        if (
            sorted_delivery_methods
            and order_sudo.carrier_id.id != sorted_delivery_methods[0]['id']
            and (cheapest_dm := next((
                dm for dm in order_sudo._get_delivery_methods()
                if dm.id == sorted_delivery_methods[0]['id']), None
            ))
        ):
            order_sudo._set_delivery_method(cheapest_dm)

        # Return the list of delivery methods available for the sales order.
        return {'delivery_methods': sorted_delivery_methods}