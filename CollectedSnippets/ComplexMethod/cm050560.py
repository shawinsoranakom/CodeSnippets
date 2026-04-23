def write(self, vals):
        values = vals
        for topping in values.get('topping_ids_2', []):
            topping_values = topping[2] if len(topping) > 2 else False
            if topping_values:
                topping_values.update({'topping_category': 2})
        for topping in values.get('topping_ids_3', []):
            topping_values = topping[2] if len(topping) > 2 else False
            if topping_values:
                topping_values.update({'topping_category': 3})
        if values.get('company_id'):
            self.env['lunch.order'].search([('supplier_id', 'in', self.ids)]).write({'company_id': values['company_id']})
        res = super().write(values)
        if 'active' in values:
            active_suppliers = self.filtered(lambda s: s.active)
            inactive_suppliers = self - active_suppliers
            Product = self.env['lunch.product'].with_context(active_test=False)
            Product.search([('supplier_id', 'in', active_suppliers.ids)]).write({'active': True})
            Product.search([('supplier_id', 'in', inactive_suppliers.ids)]).write({'active': False})
        if not CRON_DEPENDS.isdisjoint(values):
            # flush automatic_email_time field to call _sql_constraints
            if 'automatic_email_time' in values:
                self.flush_model(['automatic_email_time'])
            self._sync_cron()
        days_removed = [val for val in values if val in ('mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun') and not values[val]]
        if days_removed:
            self._cancel_future_days(days_removed)
        return res