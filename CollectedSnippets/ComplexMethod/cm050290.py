def _get_claimable_and_showable_rewards(self):
        self.ensure_one()
        res = self._get_claimable_rewards()
        loyality_cards = self.env['loyalty.card'].search([
            ('partner_id', '=', self.partner_id.id),
            ('program_id', 'any', self._get_program_domain()),
            '|',
                ('program_id.trigger', '=', 'with_code'),
                '&', ('program_id.trigger', '=', 'auto'), ('program_id.applies_on', '=', 'future'),
        ])
        total_is_zero = self.currency_id.is_zero(self.amount_total)
        global_discount_reward = self._get_applied_global_discount()
        for coupon in loyality_cards:
            points = self._get_real_points_for_coupon(coupon)
            for reward in coupon.program_id.reward_ids - self.order_line.reward_id:
                if (
                    reward.is_global_discount
                    and global_discount_reward
                    and self._best_global_discount_already_applied(global_discount_reward, reward)
                ):
                    continue
                if reward.reward_type == 'discount' and total_is_zero:
                    continue
                if coupon.expiration_date and coupon.expiration_date < fields.Date.today():
                    continue
                if points >= reward.required_points:
                    if coupon in res:
                        res[coupon] |= reward
                    else:
                        res[coupon] = reward
        return res