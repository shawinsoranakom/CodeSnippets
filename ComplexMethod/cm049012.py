def write(self, vals):
        self._prepare_self_order_splash_screen([vals])
        for record in self:
            if vals.get('self_ordering_mode') == 'kiosk' or (vals.get('pos_self_ordering_mode') == 'mobile' and vals.get('pos_self_ordering_service_mode') == 'counter'):
                vals['self_ordering_pay_after'] = 'each'

            if (not vals.get('module_pos_restaurant') and not record.module_pos_restaurant) and vals.get('self_ordering_mode') == 'mobile':
                vals['self_ordering_pay_after'] = 'each'

            if (
                vals.get('self_ordering_mode') == 'mobile'
                and (
                    vals.get('self_ordering_service_mode') == 'counter'
                    or (record.self_ordering_service_mode == 'counter' and vals.get('self_ordering_service_mode') != 'table')
                )
            ):
                vals['self_ordering_pay_after'] = 'each'

            if vals.get('self_ordering_mode') == 'mobile' and vals.get('self_ordering_pay_after') == 'meal':
                vals['self_ordering_service_mode'] = 'table'

        res = super().write(vals)
        self._ensure_public_attachments()
        self._prepare_self_order_custom_btn()
        return res