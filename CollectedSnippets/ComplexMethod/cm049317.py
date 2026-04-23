def cart(self, id=None, access_token=None, revive_method='', **post):
        """ Display the cart page.

        This route is responsible for the main cart management and abandoned cart revival logic.

        :param str id: The abandoned cart's id.
        :param str access_token: The abandoned cart's access token.
        :param str revive_method: The revival method for abandoned carts. Can be 'merge' or 'squash'.
        :return: The rendered cart page.
        :rtype: str
        """
        if not request.website.has_ecommerce_access():
            return request.redirect('/web/login')

        order_sudo = request.cart

        values = {}
        if id and access_token:
            abandoned_order = request.env['sale.order'].sudo().browse(int(id)).exists()
            if not abandoned_order or not consteq(abandoned_order.access_token, access_token):  # wrong token (or SO has been deleted)
                raise NotFound()
            if abandoned_order.state != 'draft':  # abandoned cart already finished
                values.update({'abandoned_proceed': True})
            elif revive_method == 'squash' or (revive_method == 'merge' and not request.session.get('sale_order_id')):  # restore old cart or merge with unexistant
                request.session['sale_order_id'] = abandoned_order.id
                return request.redirect('/shop/cart')
            elif revive_method == 'merge':
                abandoned_order.order_line.write({'order_id': request.session['sale_order_id']})
                abandoned_order.action_cancel()
            elif abandoned_order.id != request.session.get('sale_order_id'):  # abandoned cart found, user have to choose what to do
                values.update({'id': abandoned_order.id, 'access_token': abandoned_order.access_token})

        values.update({
            'website_sale_order': order_sudo,
            'date': fields.Date.today(),
            'suggested_products': [],
        })
        if order_sudo:
            order_sudo.order_line.filtered(lambda sol: sol.product_id and not sol.product_id.active).unlink()
            values['suggested_products'] = order_sudo._cart_accessories()
            values.update(self._get_express_shop_payment_values(order_sudo))

        values.update(request.website._get_checkout_step_values())
        values.update(self._cart_values(**post))
        values.update(self._prepare_order_history())
        return request.render('website_sale.cart', values)