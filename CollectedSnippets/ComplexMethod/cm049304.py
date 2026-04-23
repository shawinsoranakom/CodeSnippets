def get_gift_card_status(self, gift_code, config_id):
        card = self.search([('code', '=', gift_code)], limit=1)
        is_valid = card.exists() and (not card.expiration_date or card.expiration_date > fields.Date.today()) and card.points > 0
        is_valid = is_valid and (card.program_id.program_type == 'gift_card') and not card.partner_id
        is_valid = is_valid and len([id for id in card.history_ids.mapped('order_id') if id != 0]) == 0
        card_fields = self._load_pos_data_fields(config_id)
        return {
            'status': bool(is_valid) or not card.exists(),
            'data': {
                'loyalty.card': card.read(card_fields, load=False),
            }
        }