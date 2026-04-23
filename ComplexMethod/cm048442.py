def _compute_products_availability(self):
        pickings = self.filtered(lambda picking:
            picking.state in ('waiting', 'confirmed', 'assigned') and
            picking.picking_type_code in ('outgoing', 'internal')
        )
        pickings.products_availability_state = 'available'
        pickings.products_availability = _('Available')
        other_pickings = self - pickings
        other_pickings.products_availability = False
        other_pickings.products_availability_state = False

        all_moves = pickings.move_ids
        # Force to prefetch more than 1000 by 1000
        all_moves._fields['forecast_availability'].compute_value(all_moves)
        for picking in pickings:
            # In case of draft the behavior of forecast_availability is different : if forecast_availability < 0 then there is a issue else not.
            if any(
                move.product_id
                and move.product_id.uom_id.compare(
                    move.forecast_availability, 0 if move.state == 'draft' else move.product_qty
                ) == -1
                for move in picking.move_ids
            ):
                picking.products_availability = _('Not Available')
                picking.products_availability_state = 'late'
            else:
                forecast_date = max(picking.move_ids.filtered('forecast_expected_date').mapped('forecast_expected_date'), default=False)
                if forecast_date:
                    picking.products_availability = _('Exp %s', format_date(self.env, forecast_date))
                    picking.products_availability_state = 'late' if picking.scheduled_date and picking.scheduled_date < forecast_date else 'expected'