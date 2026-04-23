def _compute_abandoned_cart(self):
        for order in self:
            # a quotation can be considered as an abandonned cart if it is linked to a website,
            # is in the 'draft' state and has an expiration date
            if order.website_id and order.state == 'draft' and order.date_order:
                public_partner_id = order.website_id.user_id.partner_id
                # by default the expiration date is 1 hour if not specified on the website configuration
                abandoned_delay = order.website_id.cart_abandoned_delay or 1.0
                abandoned_datetime = datetime.utcnow() - relativedelta(hours=abandoned_delay)
                order.is_abandoned_cart = bool(order.date_order <= abandoned_datetime and order.partner_id != public_partner_id and order.order_line)
            else:
                order.is_abandoned_cart = False