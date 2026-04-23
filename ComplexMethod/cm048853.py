def retrieve_dashboard(self):
        result = super().retrieve_dashboard()
        three_months_ago = fields.Datetime.to_string(fields.Datetime.now() - relativedelta(months=3))

        purchases = self.env['purchase.order'].search_fetch(
            [('state', '=', 'purchase'), ('date_planned', '>=', three_months_ago)],
            ['date_planned', 'effective_date', 'user_id'])

        otd_purchase_count = 0
        my_purchase_count = 0
        my_otd_purchase_count = 0
        for po in purchases:
            if po.user_id == self.env.user:
                my_purchase_count += 1
            if not po.effective_date or po.effective_date > po.date_planned:
                continue
            otd_purchase_count += 1
            if po.user_id == self.env.user:
                my_otd_purchase_count += 1

        result['global']['otd'] = _("%(otd)s %%", otd=float_repr(otd_purchase_count / len(purchases) * 100 if purchases else 100, precision_digits=0))
        result['my']['otd'] = _("%(otd)s %%", otd=float_repr(my_otd_purchase_count / my_purchase_count * 100 if my_purchase_count else 100, precision_digits=0))
        result['days_to_purchase'] = self.env.company.days_to_purchase
        return result