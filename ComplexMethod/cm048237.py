def _compute_loyalty_data(self):
        self.loyalty_data = {}

        confirmed_so = self.filtered(lambda order: order.state == 'sale' and bool(order.id))
        if not confirmed_so:
            return

        loyalty_history_data = self.env['loyalty.history'].sudo()._read_group(
            domain=[
                ('order_id', 'in', confirmed_so.ids),
                ('order_model', '=', self._name),
            ],
            groupby=['order_id'],
            aggregates=['issued:sum', 'used:sum'],
        )
        loyalty_history_data_per_order = {
            order_id: {
                'total_issued': issued,
                'total_cost': cost,
            }
            for order_id, issued, cost in loyalty_history_data
        }
        for order in confirmed_so:
            if order.id not in loyalty_history_data_per_order:
                continue
            coupons = order.coupon_point_ids.coupon_id
            coupon_point_name = (len(coupons) == 1 and coupons.point_name) or _("Points")
            order.loyalty_data = {
                'point_name': coupon_point_name,
                'issued': loyalty_history_data_per_order[order.id]['total_issued'],
                'cost': loyalty_history_data_per_order[order.id]['total_cost'],
            }