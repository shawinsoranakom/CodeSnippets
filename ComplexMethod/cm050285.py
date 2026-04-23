def pricelist(self, promo, reward_id=None, **post):
        if not (order_sudo := request.cart):
            return request.redirect('/shop')
        coupon_status = order_sudo._try_apply_code(promo)
        if coupon_status.get('not_found'):
            return super().pricelist(promo, **post)
        elif coupon_status.get('error'):
            request.session['error_promo_code'] = coupon_status['error']
        elif 'error' not in coupon_status:
            reward_successfully_applied = True
            if len(coupon_status) == 1:
                coupon, rewards = next(iter(coupon_status.items()))
                if len(rewards) == 1:
                    reward = rewards
                else:
                    reward = reward_id in rewards.ids and rewards.browse(reward_id)
                if reward and (not reward.multi_product or request.env.context.get('product_id')):
                    reward_successfully_applied = self._apply_reward(order_sudo, reward, coupon)

            if reward_successfully_applied:
                request.session['successful_code'] = promo
        return request.redirect(post.get('r', '/shop/cart'))