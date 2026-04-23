def add_loyalty_history_lines(self, coupon_data, coupon_updates):
        id_mapping = {item['old_id']: int(item['id']) for item in coupon_updates}
        history_lines_create_vals = []
        for coupon in coupon_data:
            card_id = id_mapping.get(int(coupon['card_id']), False) or int(coupon['card_id'])
            if not self.env['loyalty.card'].browse(card_id).exists():
                continue
            issued = coupon['won']
            cost = coupon['spent']
            if (issued or cost) and card_id > 0:
                history_lines_create_vals.append({
                    'card_id': card_id,
                    'order_model': self._name,
                    'order_id': self.id,
                    'description': _('Onsite %s', self.display_name),
                    'used': cost,
                    'issued': issued,
                })
        self.env['loyalty.history'].create(history_lines_create_vals)