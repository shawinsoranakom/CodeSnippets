def _compute_description(self):
        for reward in self:
            reward_string = ""
            if reward.program_type == 'gift_card':
                reward_string = _("Gift Card")
            elif reward.program_type == 'ewallet':
                reward_string = _("eWallet")
            elif reward.reward_type == 'product':
                products = reward.reward_product_ids
                if len(products) == 0:
                    reward_string = _("Free Product")
                elif len(products) == 1:
                    reward_string = _("Free Product - %s", reward.reward_product_id.with_context(display_default_code=False).display_name)
                else:
                    reward_string = _("Free Product - [%s]", ', '.join(products.with_context(display_default_code=False).mapped('display_name')))
            elif reward.reward_type == 'discount':
                format_string = "%(amount)g %(symbol)s"
                if reward.currency_id.position == 'before':
                    format_string = "%(symbol)s %(amount)g"
                formatted_amount = format_string % {'amount': reward.discount, 'symbol': reward.currency_id.symbol}
                if reward.discount_mode == 'percent':
                    reward_string = _("%g%% on ", reward.discount)
                elif reward.discount_mode == 'per_point':
                    reward_string = _("%s per point on ", formatted_amount)
                elif reward.discount_mode == 'per_order':
                    reward_string = _("%s on ", formatted_amount)
                if reward.discount_applicability == 'order':
                    reward_string += _("your order")
                elif reward.discount_applicability == 'cheapest':
                    reward_string += _("the cheapest product")
                elif reward.discount_applicability == 'specific':
                    product_available = self.env['product.product'].search(reward._get_discount_product_domain(), limit=2)
                    if len(product_available) == 1:
                        reward_string += product_available.with_context(display_default_code=False).display_name
                    else:
                        reward_string += _("specific products")
                if reward.discount_max_amount:
                    format_string = "%(amount)g %(symbol)s"
                    if reward.currency_id.position == 'before':
                        format_string = "%(symbol)s %(amount)g"
                    formatted_amount = format_string % {'amount': reward.discount_max_amount, 'symbol': reward.currency_id.symbol}
                    reward_string += _(" (Max %s)", formatted_amount)
            reward.description = reward_string