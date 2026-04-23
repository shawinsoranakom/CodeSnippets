def test_discount_max_amount_on_specific_product(self):
        product_a = self.product_A
        product_b = self.product_B
        product_a.write({'taxes_id': [Command.set(self.tax_20pc_excl.ids)]})
        product_b.write({'list_price': -20, 'taxes_id': [Command.set(self.tax_20pc_excl.ids)]})

        self.env['loyalty.program'].search([]).write({'active': False})
        promotion = self.env['loyalty.program'].create({
            'name': '10% Discount',
            'program_type': 'promotion',
            'trigger': 'auto',
            'rule_ids': [Command.create({'reward_point_amount': 1, 'reward_point_mode': 'unit'})],
            'reward_ids': [Command.create({
                'discount': 10.0,
                'discount_max_amount': 9,
                'discount_applicability': 'specific',
                'discount_product_ids': [product_a.id],
            })],
        })

        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [Command.create({'product_id': product_a.id})],
        })
        self.assertEqual(order.reward_amount, 0)

        self._auto_rewards(order, promotion)
        reward_amount_tax_included = sum(l.price_total for l in order.order_line if l.reward_id)
        msg = "Max discount amount reached, the reward amount should be the max amount value."
        self.assertEqual(reward_amount_tax_included, -9, msg)

        order.order_line = [Command.clear(), Command.create({'product_id': product_b.id})]
        self._auto_rewards(order, promotion)
        reward_amount_tax_included = sum(l.price_total for l in order.order_line if l.reward_id)
        msg = "This product is not eligible to the discount."
        self.assertEqual(reward_amount_tax_included, 0, msg=msg)

        order.order_line = [
            Command.clear(),
            Command.create({'product_id': product_a.id}),  # price_total = 120
            Command.create({'product_id': product_b.id}),  # price_total = -20
        ]
        self._auto_rewards(order, promotion)
        reward_amount_tax_included = sum(l.price_total for l in order.order_line if l.reward_id)
        msg = "Reward amount above the max amount, the reward should be the max amount value."
        self.assertEqual(reward_amount_tax_included, -9, msg)

        order.order_line = [
            Command.clear(),
            Command.create({'product_id': product_a.id}),                     # price_total = 120
            Command.create({'product_id': product_b.id, 'price_unit': -95}),  # price_total = -114
        ]
        self._auto_rewards(order, promotion)
        reward_amount_tax_included = sum(l.price_total for l in order.order_line if l.reward_id)
        msg = "Reward amount should never surpass the order's current total amount."
        self.assertEqual(reward_amount_tax_included, -6, msg)

        order.order_line = [
            Command.clear(),
            Command.create({'product_id': product_a.id, 'price_unit': 50}),  # price_total = 60
            Command.create({'product_id': product_b.id, 'price_unit': -5}),  # price_total = -6
        ]
        self._auto_rewards(order, promotion)
        reward_amount_tax_included = sum(l.price_total for l in order.order_line if l.reward_id)
        msg = "Reward amount should be the percentage one if under the max amount discount."
        self.assertEqual(reward_amount_tax_included, -6, msg)