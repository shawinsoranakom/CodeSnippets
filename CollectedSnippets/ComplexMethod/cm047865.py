def _get_availabilities(self, product, quantity, product_info, bom_key, quantities_info, level, ignore_stock=False, components=False, bom_line=None, report_line=False):
        # Get availabilities according to stock (today & forecasted).
        stock_state, stock_delay = ('unavailable', False)
        if not ignore_stock:
            stock_state, stock_delay = self._get_stock_availability(product, quantity, product_info, quantities_info, bom_line=bom_line)

        # Get availabilities from applied resupply rules
        components = components or []
        route_info = product_info[product.id].get(bom_key)
        resupply_state, resupply_delay = ('unavailable', False)
        if product and not product.is_storable:
            resupply_state, resupply_delay = ('available', 0)
        elif route_info:
            resupply_state, resupply_delay = self._get_resupply_availability(route_info, components)

        if resupply_state == "unavailable" and route_info == {} and components and report_line and report_line['phantom_bom']:
            val = self._get_last_availability(report_line)
            return val

        base = {
            'resupply_avail_delay': resupply_delay,
            'stock_avail_state': stock_state,
        }
        if level != 0 and stock_state != 'unavailable':
            return {**base, **{
                'availability_display': self._format_date_display(stock_state, stock_delay),
                'availability_state': stock_state,
                'availability_delay': stock_delay,
            }}
        return {**base, **{
            'availability_display': self._format_date_display(resupply_state, resupply_delay),
            'availability_state': resupply_state,
            'availability_delay': resupply_delay,
        }}