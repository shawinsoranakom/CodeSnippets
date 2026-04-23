def action_confirm(self):
        """
        Override to validate and update coupon rewards.

        If called with one SO, checks if there exists rewards that are available but not claimed,
        and if so returns a notification action.

        :raises ValidationError: A coupon gave a negative amount of points.
        :return: True or a notification action
        :rtype: bool | dict
        """
        for order in self:
            all_coupons = order.applied_coupon_ids | order.coupon_point_ids.coupon_id | order.order_line.coupon_id
            if any(order._get_real_points_for_coupon(coupon) < 0 for coupon in all_coupons):
                raise ValidationError(_("One or more rewards on the sale order is invalid. Please check them."))
            order._update_programs_and_rewards()
            order._add_loyalty_history_lines()
        has_claimable_rewards = len(self) == 1 and bool(self._get_claimable_rewards())

        # Remove any coupon from 'current' program that don't claim any reward.
        # This is to avoid ghost coupons that are lost forever.
        # Claiming a reward for that program will require either an automated check or a manual input again.
        reward_coupons = self.order_line.coupon_id
        self.coupon_point_ids.filtered(
            lambda pe: pe.coupon_id.program_id.applies_on == 'current' and pe.coupon_id not in reward_coupons
        ).coupon_id.sudo().unlink()
        # Add/remove the points to our coupons
        for coupon, change in self.filtered(lambda s: s.state != 'sale')._get_point_changes().items():
            coupon.points += change
        res = super().action_confirm()
        # Prioritize any action from super()
        if isinstance(res, bool) and has_claimable_rewards:
            res = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'info',
                    'title': _("Rewards Available"),
                    'message': _("There are available rewards not added to this order."),
                    'next': {'type': 'ir.actions.act_window_close'},
                },
            }
        self._send_reward_coupon_mail()
        return res