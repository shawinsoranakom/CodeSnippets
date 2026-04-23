def _get_stock_availability(self, product, quantity, product_info, quantities_info, bom_line=None):
        closest_forecasted = None
        if bom_line:
            closest_forecasted = self.env.context.get('components_closest_forecasted', {}).get(product.id, {}).get(bom_line.id)
        if closest_forecasted == date.min:
            return ('available', 0)
        if closest_forecasted == date.max:
            return ('unavailable', False)
        date_today = self.env.context.get('from_date', fields.Date.today())
        if product and not product.is_storable:
            return ('available', 0)

        stock_loc = quantities_info['stock_loc']
        product_info[product.id]['consumptions'][stock_loc] += quantity
        # Check if product is already in stock with enough quantity
        if product and product.uom_id.compare(product_info[product.id]['consumptions'][stock_loc], quantities_info['free_qty']) <= 0:
            return ('available', 0)

        # No need to check forecast if the product isn't located in our stock
        if stock_loc == 'in_stock':
            domain = [('state', '=', 'forecast'), ('date', '>=', date_today), ('product_id', '=', product.id), ('product_qty', '>=', product_info[product.id]['consumptions'][stock_loc])]
            if self.env.context.get('warehouse_id'):
                domain.append(('warehouse_id', '=', self.env.context.get('warehouse_id')))

            # Seek the closest date in the forecast report where consummed quantity >= forecasted quantity
            if not closest_forecasted:
                [closest_forecasted] = self.env['report.stock.quantity']._read_group(domain, aggregates=['date:min'])[0]
            if closest_forecasted:
                days_to_forecast = (closest_forecasted - date_today).days
                return ('expected', days_to_forecast)
        return ('unavailable', False)