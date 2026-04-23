def _get_reward_values_discount(self, reward, coupon, **kwargs):
        self.ensure_one()
        assert reward.reward_type == 'discount'

        reward_applies_on = reward.discount_applicability
        reward_product = reward.discount_line_product_id
        reward_program = reward.program_id
        reward_currency = reward.currency_id
        sequence = max(
            self.order_line.filtered(lambda x: not x.is_reward_line).mapped('sequence'),
            default=10
        ) + 1
        base_reward_line_values = {
            'product_id': reward_product.id,
            'product_uom_qty': 1.0,
            'tax_ids': [Command.clear()],
            'name': reward.description,
            'reward_id': reward.id,
            'coupon_id': coupon.id,
            'sequence': sequence,
            'reward_identifier_code': _generate_random_reward_code(),
        }

        discountable = 0
        discountable_per_tax = defaultdict(int)
        if reward_applies_on == 'order':
            discountable, discountable_per_tax = self._discountable_order(reward)
        elif reward_applies_on == 'specific':
            discountable, discountable_per_tax = self._discountable_specific(reward)
        elif reward_applies_on == 'cheapest':
            discountable, discountable_per_tax = self._discountable_cheapest(reward)

        if not discountable:
            if not reward_program.is_payment_program and any(line.reward_id.program_id.is_payment_program for line in self.order_line):
                return [{
                    **base_reward_line_values,
                    'name': _("TEMPORARY DISCOUNT LINE"),
                    'price_unit': 0,
                    'product_uom_qty': 0,
                    'points_cost': 0,
                }]
            raise UserError(_("There is nothing to discount"))

        max_discount = reward_currency._convert(reward.discount_max_amount, self.currency_id, self.company_id, fields.Date.today()) or float('inf')
        # discount should never surpass the order's current total amount
        max_discount = min(self.amount_total, max_discount)
        if reward.discount_mode == 'per_point':
            points = self._get_real_points_for_coupon(coupon)
            if not reward_program.is_payment_program:
                # Rewards cannot be partially offered to customers
                points = points // reward.required_points * reward.required_points
            max_discount = min(max_discount,
                reward_currency._convert(reward.discount * points,
                    self.currency_id, self.company_id, fields.Date.today()))
        elif reward.discount_mode == 'per_order':
            max_discount = min(max_discount,
                reward_currency._convert(reward.discount, self.currency_id, self.company_id, fields.Date.today()))
        elif reward.discount_mode == 'percent':
            max_discount = min(max_discount, discountable * (reward.discount / 100))

        # Discount per taxes
        point_cost = reward.required_points if not reward.clear_wallet else self._get_real_points_for_coupon(coupon)
        if reward.discount_mode == 'per_point' and not reward.clear_wallet:
            # Calculate the actual point cost if the cost is per point
            converted_discount = self.currency_id._convert(min(max_discount, discountable), reward_currency, self.company_id, fields.Date.today())
            point_cost = coupon.currency_id.round(converted_discount / reward.discount)

        if reward_program.is_payment_program:  # Gift card / eWallet
            reward_line_values = {
                **base_reward_line_values,
                'price_unit': -min(max_discount, discountable),
                'points_cost': point_cost,
            }

            if reward_program.program_type == 'gift_card':
                # For gift cards, the SOL should consider the discount product taxes
                taxes_to_apply = reward_product.taxes_id._filter_taxes_by_company(self.company_id)
                if taxes_to_apply:
                    mapped_taxes = self.fiscal_position_id.map_tax(taxes_to_apply)
                    price_incl_taxes = mapped_taxes.filtered('price_include')
                    tax_res = mapped_taxes.with_context(
                        force_price_include=True,
                        round=False,
                        round_base=False,
                    ).compute_all(
                        reward_line_values['price_unit'],
                        currency=self.currency_id,
                    )
                    new_price = tax_res['total_excluded']
                    new_price += sum(
                        tax_data['amount']
                        for tax_data in tax_res['taxes']
                        if tax_data['id'] in price_incl_taxes.ids
                    )
                    reward_line_values.update({
                        'price_unit': new_price,
                        'tax_ids': [Command.set(mapped_taxes.ids)],
                    })
            return [reward_line_values]

        discount_factor = min(1, (max_discount / discountable)) if discountable else 1
        reward_dict = {}
        for tax, price in discountable_per_tax.items():
            if not price:
                continue
            mapped_taxes = self.fiscal_position_id.map_tax(tax)
            tax_desc = ''
            if len(discountable_per_tax) > 1 and any(t.name for t in mapped_taxes):
                tax_desc = _(
                    " - On products with the following taxes: %(taxes)s",
                    taxes=", ".join(mapped_taxes.mapped('name')),
                )
            reward_dict[tax] = {
                **base_reward_line_values,
                'name': _(
                    "Discount %(desc)s%(tax_str)s",
                    desc=reward.description,
                    tax_str=tax_desc,
                ) if mapped_taxes else reward.description,
                'price_unit': -(price * discount_factor),
                'points_cost': 0,
                'tax_ids': [Command.clear()] + [Command.link(tax.id) for tax in mapped_taxes]
            }
        # We only assign the point cost to one line to avoid counting the cost multiple times
        if reward_dict:
            reward_dict[next(iter(reward_dict))]['points_cost'] = point_cost
        # Returning .values() directly does not return a subscribable list
        return list(reward_dict.values())