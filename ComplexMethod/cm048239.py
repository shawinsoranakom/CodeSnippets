def _get_reward_values_product(self, reward, coupon, product=None, **kwargs):
        """
        Returns an array of dict containing the values required for the reward lines
        """
        self.ensure_one()
        assert reward.reward_type == 'product'

        reward_products = reward.reward_product_ids
        product = product or reward_products[:1]
        if not product or product not in reward_products:
            raise UserError(_("Invalid product to claim."))
        taxes = self.fiscal_position_id.map_tax(product.taxes_id._filter_taxes_by_company(self.company_id))
        points = self._get_real_points_for_coupon(coupon)
        claimable_count = float_round(points / reward.required_points, precision_rounding=1, rounding_method='DOWN') if not reward.clear_wallet else 1
        cost = points if reward.clear_wallet else claimable_count * reward.required_points
        return [{
            'name': reward.description,
            'product_id': product.id,
            'discount': 100,
            'product_uom_qty': reward.reward_product_qty * claimable_count,
            'reward_id': reward.id,
            'coupon_id': coupon.id,
            'points_cost': cost,
            'reward_identifier_code': _generate_random_reward_code(),
            'sequence': max(self.order_line.filtered(lambda x: not x.is_reward_line).mapped('sequence'), default=10) + 1,
            'tax_ids': [Command.clear()] + [Command.link(tax.id) for tax in taxes],
        }]