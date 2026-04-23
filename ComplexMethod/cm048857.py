def _get_lead_days(self, product, **values):
        """Add the supplier delay to the cumulative delay and cumulative description.
        """
        delays, delay_description = super()._get_lead_days(product, **values)
        bypass_delay_description = self.env.context.get('bypass_delay_description')
        buy_rule = self.filtered(lambda r: r.action == 'buy')
        seller = 'supplierinfo' in values and values['supplierinfo'] or product.with_company(buy_rule.company_id)._select_seller(quantity=None)
        if not buy_rule:
            return delays, delay_description
        if not seller:
            delays['total_delay'] += 365
            delays['no_vendor_found_delay'] += 365
            if not bypass_delay_description:
                delay_description.append((_('No Vendor Found'), _('+ %s day(s)', 365)))
            return delays, delay_description
        buy_rule.ensure_one()
        if not self.env.context.get('ignore_vendor_lead_time'):
            supplier_delay = seller[:1].delay
            delays['total_delay'] += supplier_delay
            delays['purchase_delay'] += supplier_delay
            if not bypass_delay_description:
                delay_description.append((_('Receipt Date'), supplier_delay))
                delay_description.append((_('Vendor Lead Time'), _('+ %d day(s)', supplier_delay)))
        days_to_order = buy_rule.company_id.days_to_purchase
        delays['total_delay'] += days_to_order
        if not bypass_delay_description:
            delay_description.append((_('Order Deadline'), days_to_order))
            delay_description.append((_('Days to Purchase'), _('+ %d day(s)', days_to_order)))
        return delays, delay_description