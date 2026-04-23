def claim_reward(self, reward_id, code=None, **post):
        redirect = post.get('r', '/shop/cart')
        if not (order_sudo := request.cart):
            return request.redirect(redirect)

        try:
            reward_id = int(reward_id)
        except ValueError:
            reward_id = None

        reward_sudo = request.env['loyalty.reward'].sudo().browse(reward_id).exists()
        if not reward_sudo:
            return request.redirect(redirect)

        if reward_sudo.multi_product and 'product_id' in post:
            request.update_context(product_id=int(post['product_id']))
        else:
            request.redirect(redirect)

        program_sudo = reward_sudo.program_id
        claimable_rewards = order_sudo._get_claimable_and_showable_rewards()
        coupon = request.env['loyalty.card']
        for coupon_, rewards in claimable_rewards.items():
            if reward_sudo in rewards:
                coupon = coupon_
                if code == coupon.code and (
                    (program_sudo.trigger == 'with_code' and program_sudo.program_type != 'promo_code')
                    or (program_sudo.trigger == 'auto'
                        and program_sudo.applies_on == 'future'
                        and program_sudo.program_type not in ('ewallet', 'loyalty'))
                ):
                    return self.pricelist(code, reward_id=reward_id)
        if coupon:
            self._apply_reward(order_sudo, reward_sudo, coupon)
        return request.redirect(redirect)