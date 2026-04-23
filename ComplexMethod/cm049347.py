def _filter_can_send_abandoned_cart_mail(self):
        self.website_id.ensure_one()
        abandoned_datetime = datetime.utcnow() - relativedelta(hours=self.website_id.cart_abandoned_delay)

        sales_after_abandoned_date = self.env['sale.order'].search([
            ('state', '=', 'sale'),
            ('partner_id', 'in', self.partner_id.ids),
            ('create_date', '>=', abandoned_datetime),
            ('website_id', '=', self.website_id.id),
        ])
        latest_create_date_per_partner = {}
        for sale in self:
            if sale.partner_id not in latest_create_date_per_partner:
                latest_create_date_per_partner[sale.partner_id] = sale.create_date
            else:
                latest_create_date_per_partner[sale.partner_id] = max(latest_create_date_per_partner[sale.partner_id], sale.create_date)
        has_later_sale_order = {}
        for sale in sales_after_abandoned_date:
            if has_later_sale_order.get(sale.partner_id, False):
                continue
            has_later_sale_order[sale.partner_id] = latest_create_date_per_partner[sale.partner_id] <= sale.date_order

        # Customer needs to be signed in otherwise the mail address is not known.
        # We therefore consider only sales with a known mail address.

        # If a payment processing error occurred when the customer tried to complete their checkout,
        # then the email won't be sent.

        # If all the products in the checkout are free, and the customer does not visit the shipping page to add a
        # shipping fee or the shipping fee is also free, then the email won't be sent.

        # If a potential customer creates one or more abandoned sale order and then completes a sale order before
        # the recovery email gets sent, then the email won't be sent.

        return self.filtered(
            lambda abandoned_sale_order:
            abandoned_sale_order.partner_id.email
            and not any(transaction.sudo().state == 'error' for transaction in abandoned_sale_order.transaction_ids)
            and any(not float_is_zero(line.price_unit, precision_rounding=line.currency_id.rounding) for line in abandoned_sale_order.order_line)
            and not has_later_sale_order.get(abandoned_sale_order.partner_id, False)
        )