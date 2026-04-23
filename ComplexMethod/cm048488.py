def _match_searched_availability(self, operator, value, get_comparison_date):
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

        if not value:
            raise UserError(_('Search not supported without a value.'))

        # We consider an operation without any moves as always available since there is no goods to wait.
        if len(self) == 0:
            is_selected_available = any(val == 'available' for val in value) if isinstance(value, list) else value == 'available'
            if is_selected_available == (operator in {'=', 'in'}):
                return True
            return False
        moves = self
        if operator == '=':
            moves = get_stock_moves(moves, value)
        elif operator == '!=':
            moves = moves - get_stock_moves(moves, value)
        elif operator == 'in':
            search_moves = self.env['stock.move']
            for state in value:
                search_moves |= get_stock_moves(moves, state)
            moves = search_moves
        elif operator == 'not in':
            search_moves = self.env['stock.move']
            for state in value:
                search_moves |= get_stock_moves(moves, state)
            moves = self - search_moves
        else:
            raise UserError(_('Operation not supported'))
        return bool(moves)