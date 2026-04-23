def _prepare_order_history(self):
        """Prepare the order history of the current user.

        The valid order lines of the last 10 confirmed orders are considered and grouped by date. An
        order line is not valid if:

        - Its product is already in the cart.
        - It's a combo parent line.
        - It has an unsellable product.
        - It has a zero-priced product (if the website blocks them).
        - It has an already seen product (duplicate or identical combo).

        The dates are represented by labels like "Today", "Yesterday", or "X days ago".

        :return: The order history, in the format
                 {'order_history': [{'label': str, 'lines': SaleOrderLine}, ...]}.
        :rtype: dict
        """
        def is_same_combo(line1_, line2_):
            """Check if two combo lines have the same linked product combination."""
            return line1_.linked_line_ids.product_id.ids == line2_.linked_line_ids.product_id.ids

        # Get the last 10 confirmed orders from the current website user.
        previous_orders_lines_sudo = request.env['sale.order'].sudo().search(
            [
                ('partner_id', '=', request.env.user.partner_id.id),
                ('state', '=', 'sale'),
                ('website_id', '=', request.website.id),
            ],
            order='date_order desc',
            limit=10,
        ).order_line

        # Prepare the order history.
        SaleOrderLineSudo = request.env['sale.order.line'].sudo()
        cart_lines_sudo = request.cart.order_line if request.cart else SaleOrderLineSudo
        seen_lines_sudo = SaleOrderLineSudo
        lines_per_order_date = {}
        for line_sudo in previous_orders_lines_sudo:
            # Ignore lines that are combo parents, unsellable, or zero-priced.
            product_id = line_sudo.product_id.id
            if (
                line_sudo.linked_line_id.product_type == 'combo'
                or not line_sudo._is_sellable()
                or (
                    request.website.prevent_zero_price_sale
                    and line_sudo.product_id._get_combination_info_variant()['price'] == 0
                )
            ):
                continue

            # Ignore lines that are already in the cart or have already been seen.
            is_combo = line_sudo.product_type == 'combo'
            if any(
                l.product_id.id == product_id and (not is_combo or is_same_combo(line_sudo, l))
                for l in cart_lines_sudo + seen_lines_sudo
            ):
                continue
            seen_lines_sudo |= line_sudo

            # Group lines by date.
            days_ago = (fields.Date.today() - line_sudo.order_id.date_order.date()).days
            if days_ago == 0:
                line_group_label = self.env._("Today")
            elif days_ago == 1:
                line_group_label = self.env._("Yesterday")
            else:
                line_group_label = self.env._("%s days ago", days_ago)
            lines_per_order_date.setdefault(line_group_label, SaleOrderLineSudo)
            lines_per_order_date[line_group_label] |= line_sudo

        # Flatten the line groups to get the final order history.
        return {
            'order_history': [
                {'label': label, 'lines': lines} for label, lines in lines_per_order_date.items()
            ]
        }