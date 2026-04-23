def _get_lead_days(self, product, **values):
        """Add the product and company manufacture delay to the cumulative delay
        and cumulative description.
        """
        delays, delay_description = super()._get_lead_days(product, **values)
        bypass_delay_description = self.env.context.get('bypass_delay_description')
        manufacture_rule = self.filtered(lambda r: r.action == 'manufacture')
        if not manufacture_rule:
            return delays, delay_description
        manufacture_rule.ensure_one()
        bom = values.get('bom') or self.env['mrp.bom']._bom_find(product, picking_type=manufacture_rule.picking_type_id, company_id=manufacture_rule.company_id.id)[product]
        if not bom:
            delays['total_delay'] += 365
            delays['no_bom_found_delay'] += 365
            if not bypass_delay_description:
                delay_description.append((_('No BoM Found'), _('+ %s day(s)', 365)))
        manufacture_delay = bom.produce_delay
        delays['total_delay'] += manufacture_delay
        delays['manufacture_delay'] += manufacture_delay
        if not bypass_delay_description:
            delay_description.append((_('Production End Date'), manufacture_delay))
            delay_description.append((_('Manufacturing Lead Time'), _('+ %d day(s)', manufacture_delay)))
        if bom.type == 'normal':
            # pre-production rules
            warehouse = self.location_dest_id.warehouse_id
            for wh in warehouse:
                if wh.manufacture_steps != 'mrp_one_step':
                    wh_manufacture_rules = product._get_rules_from_location(product.property_stock_production, route_ids=wh.pbm_route_id)
                    extra_delays, extra_delay_description = (wh_manufacture_rules - self).with_context(global_horizon_days=0)._get_lead_days(product, **values)
                    for key, value in extra_delays.items():
                        delays[key] += value
                    delay_description += extra_delay_description
        days_to_order = values.get('days_to_order', bom.days_to_prepare_mo)
        delays['total_delay'] += days_to_order
        if not bypass_delay_description:
            delay_description.append((_('Production Start Date'), days_to_order))
            delay_description.append((_('Days to Supply Components'), _('+ %d day(s)', days_to_order)))
        return delays, delay_description