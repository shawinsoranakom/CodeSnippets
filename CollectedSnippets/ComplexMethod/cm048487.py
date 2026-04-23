def _get_forecast_availability_outgoing(self, warehouse, location_id=False):
        """ Get forcasted information (sum_qty_expected, max_date_expected) of self for the warehouse's locations.
        :param warehouse: warehouse to search under
        :param  location_id: location source of outgoing moves
        :return: a defaultdict of outgoing moves from warehouse for product_id in self, values are tuple (sum_qty_expected, max_date_expected)
        :rtype: defaultdict
        """
        wh_location_query = self.env['stock.location']._search([('id', 'child_of', warehouse.view_location_id.id)])
        forecast_lines = self.env['stock.forecasted_product_product']._get_report_lines(False, self.product_id.ids, wh_location_query, location_id or warehouse.lot_stock_id, read=False)
        result = defaultdict(lambda: (0.0, False))
        for line in forecast_lines:
            move_out = line.get('move_out')
            if not move_out or not line['quantity']:
                continue
            move_in = line.get('move_in')
            qty_expected = line['quantity'] + result[move_out][0] if line['replenishment_filled'] else -line['quantity']
            date_expected = False
            if move_in:
                date_expected = max(move_in.date, result[move_out][1]) if result[move_out][1] else move_in.date
            result[move_out] = (qty_expected, date_expected)

        return result