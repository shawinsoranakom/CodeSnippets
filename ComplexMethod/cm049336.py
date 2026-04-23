def shop_payment_validate(self, sale_order_id=None, **post):
        """ Method that should be called by the server when receiving an update
        for a transaction. State at this point :

         - UDPATE ME
        """
        if sale_order_id is None:
            order_sudo = request.cart
            if not order_sudo and 'sale_last_order_id' in request.session:
                # Retrieve the last known order from the session if the session key `sale_order_id`
                # was prematurely cleared. This is done to prevent the user from updating their cart
                # after payment in case they don't return from payment through this route.
                last_order_id = request.session['sale_last_order_id']
                order_sudo = request.env['sale.order'].sudo().browse(last_order_id).exists()
        else:
            order_sudo = request.env['sale.order'].sudo().browse(sale_order_id)
            assert order_sudo.id == request.session.get('sale_last_order_id')

        if not order_sudo:
            return request.redirect(self._get_shop_path())

        errors = self._get_shop_payment_errors(order_sudo) if order_sudo.state != 'sale' else []
        if errors:
            first_error = errors[0]  # only display first error
            error_msg = f"{first_error[0]}\n{first_error[1]}"
            raise ValidationError(error_msg)

        tx_sudo = order_sudo.get_portal_last_transaction()
        if order_sudo.amount_total and not tx_sudo:
            return request.redirect(self._get_shop_path())

        if not order_sudo.amount_total and not tx_sudo and order_sudo.state != 'sale':
            order_sudo._check_cart_is_ready_to_be_paid()
            # Only confirm the order if it wasn't already confirmed.
            order_sudo._validate_order()

        # clean context and session, then redirect to the confirmation page
        request.website.sale_reset()
        if tx_sudo and tx_sudo.state == 'draft':
            return request.redirect(self._get_shop_path())

        return request.redirect('/shop/confirmation')