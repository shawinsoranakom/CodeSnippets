def get_statistics_for_session(self, session):
        self.ensure_one()
        currency = self.currency_id
        timezone = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
        statistics = {
            'cash': {
                'raw_opening_cash': session.cash_register_balance_start,
                'opening_cash': currency.format(session.cash_register_balance_start)
            },
            'date': {
                'is_started': bool(session.start_at),
                'start_date': session.start_at.astimezone(timezone).strftime('%b %d') if session.start_at else False,
            },
            'orders': {
                'paid': False,
                'draft': False,
            },
        }

        all_paid_orders = session.order_ids.filtered(lambda o: o.state in ['paid', 'done'])
        refund_orders = all_paid_orders.filtered(lambda o: o.is_refund)
        draft_orders = session.order_ids.filtered(lambda o: o.state == 'draft')
        non_refund_orders = all_paid_orders - refund_orders

        # calculate total refunded amount per original order for refund count check
        refund_totals = defaultdict(float)
        for refund in refund_orders:
            if refund.refunded_order_id:
                refund_totals[refund.refunded_order_id.id] += abs(refund.amount_total)

        # count paid orders that are not completely refunded
        paid_order_count = sum(
            1 for order in non_refund_orders
            if refund_totals.get(order.id, 0.0) != order.amount_total
        )

        if paid_order_count:
            total_paid = sum(all_paid_orders.mapped('amount_total'))
            statistics['orders']['paid'] = {
                'amount': total_paid,
                'count': paid_order_count,
                'display': f"{currency.format(total_paid)} ({paid_order_count} {'order' if paid_order_count == 1 else 'orders'})"
            }

        if draft_orders:
            total_draft = sum(draft_orders.mapped('amount_total'))
            count_draft = len(draft_orders)
            statistics['orders']['draft'] = {
                'amount': total_draft,
                'count': count_draft,
                'display': f"{currency.format(total_draft)} ({count_draft} {'order' if count_draft == 1 else 'orders'})"
            }

        return statistics