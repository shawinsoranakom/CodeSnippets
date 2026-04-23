def _make_po_get_domain(self, company_id, values, partner):
        currency = ('supplier' in values and values['supplier'].currency_id) or \
                   partner.with_company(company_id).property_purchase_currency_id or \
                   company_id.currency_id
        domain = (
            ('partner_id', '=', partner.id),
            ('state', '=', 'draft'),
            ('picking_type_id', '=', self.picking_type_id.id),
            ('company_id', '=', company_id.id),
            ('user_id', '=', partner.buyer_id.id),
            ('currency_id', '=', currency.id),
        )
        if partner.group_rfq == 'default' or self.picking_type_id.code == 'dropship':
            if values.get('reference_ids'):
                domain += (('reference_ids', 'in', tuple(values['reference_ids'].ids)),)
        date_planned = fields.Datetime.from_string(values['date_planned'])
        if partner.group_rfq == 'day':
            start_dt = datetime.combine(date_planned, datetime.min.time())
            end_dt = datetime.combine(date_planned, datetime.max.time())
            domain += (('date_planned', '>=', start_dt), ('date_planned', '<=', end_dt))
        if partner.group_rfq == 'week':
            if partner.group_on == 'default':
                start_dt = datetime.combine(date_planned - relativedelta(days=date_planned.isoweekday()), datetime.min.time())
                end_dt = datetime.combine(date_planned + relativedelta(days=6 - date_planned.isoweekday()), datetime.max.time())
                domain += (('date_planned', '>=', start_dt), ('date_planned', '<=', end_dt))
            else:
                delta_days = (7 + int(partner.group_on) - date_planned.isoweekday()) % 7
                date = date_planned + relativedelta(days=delta_days)
                start_dt = datetime.combine(date, datetime.min.time())
                end_dt = datetime.combine(date, datetime.max.time())
                domain += (('date_planned', '>=', start_dt), ('date_planned', '<=', end_dt))

        return domain