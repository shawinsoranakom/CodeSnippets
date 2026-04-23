def _cheapest_line(self, reward):
        self.ensure_one()
        cheapest_line = False
        cheapest_line_price_unit = False
        domain = reward._get_discount_product_domain()
        for line in (self.order_line - self._get_no_effect_on_threshold_lines()):
            line_price_unit = self._get_order_line_price(line, 'price_unit')
            if (
                line.reward_id
                or line.combo_item_id
                or not line.product_uom_qty
                or not line_price_unit
                or not line.product_id.filtered_domain(domain)
            ):
                continue
            if not cheapest_line or cheapest_line_price_unit > line_price_unit:
                cheapest_line = line._get_lines_with_price()
                cheapest_line_price_unit = line_price_unit
        return cheapest_line