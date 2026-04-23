def _get_components_closest_forecasted(self, lines, line_quantities, parent_bom, product_info, parent_product, ignore_stock=False):
        """
            Returns a dict mapping products to a dict of their corresponding BoM lines,
            which are mapped to their closest date in the forecast report where consumed quantity >= forecasted quantity.

            E.g. {'product_1_id': {'line_1_id': date_1, line_2_id: date_2}, 'product_2': {line_3_id: date_3}, ...}.

            Note that
                - if a product is unavailable + not forecasted for a specific bom line => its date will be `date.max`
                - if a product's type is not `product` or is already in stock for a specific bom line => its date will be `date.min`.
        """
        if ignore_stock:
            return {}
        # Use defaultdict(OrderedDict) in case there are lines with the same component.
        closest_forecasted = defaultdict(OrderedDict)
        remaining_products = []
        product_quantities_info = defaultdict(OrderedDict)
        for line in lines:
            product = line.product_id
            line_quantity = line_quantities.get(line.id, 0.0)
            quantities_info = self._get_quantities_info(product, line.product_uom_id, product_info, parent_bom, parent_product)
            stock_loc = quantities_info['stock_loc']
            product_info[product.id]['consumptions'][stock_loc] += line_quantity
            product_quantities_info[product.id][line.id] = product_info[product.id]['consumptions'][stock_loc]
            if (not product.is_storable or
                    product.uom_id.compare(product_info[product.id]['consumptions'][stock_loc], quantities_info['free_qty']) <= 0):
                # Use date.min as a sentinel value for _get_stock_availability
                closest_forecasted[product.id][line.id] = date.min
            elif stock_loc != 'in_stock' or quantities_info['forecasted_qty'] < line_quantity:
                closest_forecasted[product.id][line.id] = date.max
            else:
                remaining_products.append(product.id)
                closest_forecasted[product.id][line.id] = None
        date_today = self.env.context.get('from_date', fields.Date.today())
        domain = [('state', '=', 'forecast'), ('date', '>=', date_today), ('product_id', 'in', list(set(remaining_products)))]
        if self.env.context.get('warehouse_id'):
            domain.append(('warehouse_id', '=', self.env.context.get('warehouse_id')))
        if remaining_products:
            res = self.env['report.stock.quantity']._read_group(
                domain,
                groupby=['product_id', 'product_qty'],
                aggregates=['date:min'],
                order='product_id asc, date:min asc'
            )
            available_quantities = defaultdict(list)
            for group in res:
                product_id = group[0].id
                available_quantities[product_id].append([group[2], group[1]])
            for product_id in remaining_products:
                # Find the first empty line_id for the given product_id.
                line_id = next(filter(lambda k: not closest_forecasted[product_id][k], closest_forecasted[product_id].keys()), None)
                # Find the first available quantity for the given product and update closest_forecasted
                for min_date, product_qty in available_quantities[product_id]:
                    if product_qty >= product_quantities_info[product_id][line_id]:
                        closest_forecasted[product_id][line_id] = min_date
                        break
                if not closest_forecasted[product_id][line_id]:
                    closest_forecasted[product_id][line_id] = date.max
        return closest_forecasted