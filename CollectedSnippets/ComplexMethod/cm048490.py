def get_stock_moves(moves, state):
            if state == 'available':
                return moves.filtered(lambda m: m.forecast_availability == m.product_qty and not m.forecast_expected_date)
            elif state == 'expected':
                return moves.filtered(lambda m: m.forecast_availability == m.product_qty and m.forecast_expected_date and m.forecast_expected_date <= get_comparison_date(m))
            elif state == 'late':
                return moves.filtered(lambda m: m.forecast_availability == m.product_qty and m.forecast_expected_date and m.forecast_expected_date > get_comparison_date(m))
            elif state == 'unavailable':
                return moves if moves.filtered(lambda m: m.forecast_availability < m.product_qty) else self.env['stock.move']
            else:
                raise UserError(_('Selection not supported.'))