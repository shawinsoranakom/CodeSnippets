def _compute_components_availability(self):
        productions = self.filtered(lambda mo: mo.state not in ('cancel', 'done', 'draft'))
        productions.components_availability_state = 'available'
        productions.components_availability = _('Available')

        other_productions = self - productions
        other_productions.components_availability = False
        other_productions.components_availability_state = False

        all_raw_moves = productions.move_raw_ids
        # Force to prefetch more than 1000 by 1000
        all_raw_moves._fields['forecast_availability'].compute_value(all_raw_moves)
        for production in productions:
            if any(
                move.product_id
                and move.product_id.uom_id.compare(
                    move.forecast_availability,
                    0 if move.state == 'draft' else move.product_qty,
                ) == -1
                for move in production.move_raw_ids
            ):

                production.components_availability = _('Not Available')
                production.components_availability_state = 'unavailable'
            else:
                forecast_date = max(production.move_raw_ids.filtered('forecast_expected_date').mapped('forecast_expected_date'), default=False)
                if forecast_date:
                    production.components_availability = _('Exp %s', format_date(self.env, forecast_date))
                    if production.date_start:
                        production.components_availability_state = 'late' if forecast_date > production.date_start else 'expected'