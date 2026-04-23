def _validate_additional_landed_cost_lines(self, stock_landed_cost, valid_vals):
        for valuation in stock_landed_cost.valuation_adjustment_lines:
            add_cost = valuation.additional_landed_cost
            split_method = valuation.cost_line_id.split_method
            product = valuation.move_id.product_id
            if split_method == 'equal':
                self.assertEqual(add_cost, valid_vals['equal'], self._error_message(valid_vals['equal'], add_cost))
            elif split_method == 'by_quantity' and product == self.product_refrigerator:
                self.assertEqual(add_cost, valid_vals['by_quantity_refrigerator'], self._error_message(valid_vals['by_quantity_refrigerator'], add_cost))
            elif split_method == 'by_quantity' and product == self.product_oven:
                self.assertEqual(add_cost, valid_vals['by_quantity_oven'], self._error_message(valid_vals['by_quantity_oven'], add_cost))
            elif split_method == 'by_weight' and product == self.product_refrigerator:
                self.assertEqual(add_cost, valid_vals['by_weight_refrigerator'], self._error_message(valid_vals['by_weight_refrigerator'], add_cost))
            elif split_method == 'by_weight' and product == self.product_oven:
                self.assertEqual(add_cost, valid_vals['by_weight_oven'], self._error_message(valid_vals['by_weight_oven'], add_cost))
            elif split_method == 'by_volume' and product == self.product_refrigerator:
                self.assertEqual(add_cost, valid_vals['by_volume_refrigerator'], self._error_message(valid_vals['by_volume_refrigerator'], add_cost))
            elif split_method == 'by_volume' and product == self.product_oven:
                self.assertEqual(add_cost, valid_vals['by_volume_oven'], self._error_message(valid_vals['by_volume_oven'], add_cost))