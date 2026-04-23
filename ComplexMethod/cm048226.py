def _compute_parts_availability(self):
        repairs = self.filtered(lambda ro: ro.state in ('confirmed', 'under_repair'))
        repairs.parts_availability_state = 'available'
        repairs.parts_availability = _('Available')

        other_repairs = self - repairs
        other_repairs.parts_availability = False
        other_repairs.parts_availability_state = False

        all_moves = repairs.move_ids
        # Force to prefetch more than 1000 by 1000
        all_moves._fields['forecast_availability'].compute_value(all_moves)
        for repair in repairs:
            if any(
                move.product_id
                and move.product_id.uom_id.compare(
                    move.forecast_availability, move.product_qty
                ) < 0
                for move in repair.move_ids
            ):
                repair.parts_availability = _('Not Available')
                repair.parts_availability_state = 'late'
                continue
            forecast_date = max(repair.move_ids.filtered('forecast_expected_date').mapped('forecast_expected_date'), default=False)
            if not forecast_date:
                continue
            repair.parts_availability = _('Exp %s', format_date(self.env, forecast_date))
            if repair.schedule_date:
                repair.parts_availability_state = 'late' if forecast_date > repair.schedule_date else 'expected'