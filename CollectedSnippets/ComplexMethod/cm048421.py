def _get_lead_days(self, product, **values):
        """Returns the cumulative delay and its description encountered by a
        procurement going through the rules in `self`.

        :param product: the product of the procurement
        :type product: :class:`~odoo.addons.product.models.product.ProductProduct`
        :return: the cumulative delay and cumulative delay's description
        :rtype: tuple[defaultdict(float), list[str, str]]
        """
        # FIXME : ensure one product or make the method work with multiple products
        _ = self.env._
        delays = defaultdict(float)
        delay_description = []
        bypass_delay_description = self.env.context.get('bypass_delay_description')
        # Check if the rules have lead time
        delaying_rules = self.filtered(lambda r: r.action in ['pull', 'pull_push'] and r.delay)
        if delaying_rules:
            delays['total_delay'] += sum(delaying_rules.mapped('delay'))
            if not bypass_delay_description:
                delay_description = [
                    (_('Delay on %s', rule.name), _('+ %d day(s)', rule.delay))
                    for rule in delaying_rules
                ]
        # Check if there's a horizon set
        bypass_global_horizon_days = self.env.context.get('bypass_global_horizon_days')
        if bypass_global_horizon_days:
            return delays, delay_description
        global_horizon_days = self.env['stock.warehouse.orderpoint'].get_horizon_days()
        if global_horizon_days:
            delays['horizon_time'] += global_horizon_days
            if not bypass_delay_description:
                delay_description.append((_('Time Horizon'), _('+ %d day(s)', global_horizon_days)))
        return delays, delay_description