def _process_existing_gift_cards(self, coupon_data):
        updated_gift_cards = self.env['loyalty.card']
        coupon_key_to_remove = []
        for coupon_id, coupon_vals in coupon_data.items():
            program_id = self.env['loyalty.program'].browse(coupon_vals['program_id'])
            if program_id.program_type == 'gift_card':
                updated = False
                gift_card = self.env['loyalty.card'].search([
                    ('|'),
                    ('code', '=', coupon_vals.get('code', '')),
                    ('id', '=', coupon_vals.get('coupon_id', False))
                ])
                if not gift_card.exists():
                    continue

                if not gift_card.partner_id and self.partner_id:
                    updated = True
                    gift_card.partner_id = self.partner_id
                    gift_card.history_ids.create({
                        'card_id': gift_card.id,
                        'description': _('Assigning partner %s', self.partner_id.name),
                        'used': 0,
                        'issued': gift_card.points,
                    })

                if len([id for id in gift_card.history_ids.mapped('order_id') if id != 0]) == 0:
                    updated = True
                    gift_card.source_pos_order_id = self.id
                    gift_card.history_ids.create({
                        'card_id': gift_card.id,
                        'order_model': self._name,
                        'order_id': self.id,
                        'description': _('Assigning order %s', self.display_name),
                        'used': 0,
                        'issued': gift_card.points,
                    })

                if coupon_vals.get('points') != gift_card.points:
                    # Coupon vals contains negative points
                    updated = True
                    new_value = gift_card.points + coupon_vals['points']
                    gift_card.points = new_value
                    gift_card.history_ids.create({
                        'card_id': gift_card.id,
                        'order_model': self._name,
                        'order_id': self.id,
                        'description': _('Onsite %s', self.display_name),
                        'used': -coupon_vals['points'] if coupon_vals['points'] < 0 else 0,
                        'issued': coupon_vals['points'] if coupon_vals['points'] > 0 else 0,
                    })

                if updated:
                    updated_gift_cards |= gift_card

                coupon_key_to_remove.append(coupon_id)

        for key in coupon_key_to_remove:
            coupon_data.pop(key, None)

        return updated_gift_cards