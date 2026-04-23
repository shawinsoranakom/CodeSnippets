def shop_checkout(self, try_skip_step=None, **query_params):
        """ Display the checkout page.

        :param str try_skip_step: Whether the user should immediately be redirected to the next step
                                  if no additional information (i.e., address or delivery method) is
                                  required on the checkout page. 'true' or 'false'.
        :param dict query_params: The additional query string parameters.
        :return: The rendered checkout page.
        :rtype: str
        """
        try_skip_step = str2bool(try_skip_step or 'false')
        order_sudo = request.cart
        request.session['sale_last_order_id'] = order_sudo.id

        if redirection := self._check_cart_and_addresses(order_sudo):
            return redirection

        checkout_page_values = self._prepare_checkout_page_values(order_sudo, **query_params)

        can_skip_delivery = True  # Delivery is only needed for deliverable products.
        if order_sudo._has_deliverable_products():
            can_skip_delivery = False
            available_dms = order_sudo._get_delivery_methods()
            checkout_page_values['delivery_methods'] = available_dms
            if delivery_method := order_sudo._get_preferred_delivery_method(available_dms):
                rate = delivery_method.rate_shipment(order_sudo)
                if (
                    not order_sudo.carrier_id
                    or not rate.get('success')
                    or order_sudo.amount_delivery != rate['price']
                ):
                    order_sudo._set_delivery_method(delivery_method, rate=rate)

        checkout_page_values.update(
            request.website._get_checkout_step_values()
        )
        if try_skip_step and can_skip_delivery:
            return request.redirect(
                checkout_page_values['next_website_checkout_step_href']
            )

        return request.render('website_sale.checkout', checkout_page_values)