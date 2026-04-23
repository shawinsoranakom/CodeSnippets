def _compute_value(self):
        company_id = self.env.company
        self.company_currency_id = company_id.currency_id
        products = self._with_valuation_context()

        at_date = self.env.context.get('to_date')
        original_value = at_date
        at_date = fields.Datetime.to_datetime(at_date)
        if (isinstance(original_value, date) and not isinstance(original_value, datetime)) or \
            (isinstance(original_value, str) and len(original_value) == 10):
            at_date = datetime.combine(at_date.date(), time.max)

        if at_date:
            products = products.with_context(at_date=at_date, to_date=at_date)

        # PERF: Pre-compute:the sum of 'total_value' of lots per product in go
        std_price_by_company_id = {}
        total_value_by_company_id = {}
        lot_valuated_products_ids = {p.id for p in self if p.lot_valuated}
        valued_quantity_by_product_id = defaultdict(float)
        for company in self.env.companies:
            std_price_by_product_id = defaultdict(float)
            total_value_by_product_id = defaultdict(float)

            products = self.with_company(company.id).with_context(allowed_company_ids=company.ids)
            products = products._with_valuation_context()
            if at_date:
                products = products.with_context(at_date=at_date, to_date=at_date)

            env = products.env

            if lot_valuated_products_ids:
                domain = Domain([('product_id', 'in', lot_valuated_products_ids)])
                if not self.env.context.get('warehouse_id'):
                    domain &= Domain([('product_qty', '!=', 0)])
                lots_by_product = env['stock.lot']._read_group(
                    domain,
                    groupby=['product_id'],
                    aggregates=['id:recordset']
                )
                # Collect all lots and trigger batch computation of total_value
                env['stock.lot'].browse(
                        lot.id
                        for _, lots in lots_by_product
                        for lot in lots
                ).mapped('total_value')
                for product, lots in lots_by_product:
                    value = sum(lots.mapped('total_value'))
                    std_price_by_product_id[product.id] = value / product.qty_available if product.qty_available else product.standard_price
                    total_value_by_product_id[product.id] = value

            product_ids_grouped_by_cost_method = defaultdict(set)
            ratio_by_product_id = {}
            for product in products:
                if product.lot_valuated:
                    continue
                product_whole_company_context = product
                if 'warehouse_id' in self.env.context:
                    product_whole_company_context = product.with_context(warehouse_id=False)
                if product.uom_id.is_zero(product.qty_available):
                    total_value_by_product_id[product.id] = 0
                    std_price_by_product_id[product.id] = product.standard_price
                    continue
                if product.uom_id.is_zero(product_whole_company_context.qty_available):
                    total_value_by_product_id[product.id] = product.standard_price * product.qty_available
                    std_price_by_product_id[product.id] = product.standard_price
                    continue
                if product.uom_id.compare(product.qty_available, product_whole_company_context.qty_available) != 0:
                    ratio = product.qty_available / product_whole_company_context.qty_available
                    ratio_by_product_id[product.id] = ratio

                product_ids_grouped_by_cost_method[product.cost_method].add(product.id)

            for cost_method, product_ids in product_ids_grouped_by_cost_method.items():
                products_to_value = products.env['product.product'].browse(product_ids).with_context(warehouse_id=False)
                # To remove once price_unit isn't truncate in sql anymore (no need of force_recompute)
                if cost_method == 'standard':
                    std_prices, total_values = products_to_value._run_standard_batch(at_date=at_date)
                elif cost_method == 'average':
                    std_prices, total_values = products_to_value._run_average_batch(at_date=at_date)
                else:
                    std_prices, total_values = products_to_value._run_fifo_batch(at_date=at_date)

                std_price_by_product_id.update(std_prices)
                total_value_by_product_id.update(total_values)

            for product in products:
                total_value = total_value_by_product_id.get(product.id, 0)
                total_value_by_product_id[product.id] = total_value * ratio_by_product_id.get(product.id, 1)
                valued_quantity_by_product_id[product.id] += product.qty_available

            std_price_by_company_id[company.id] = std_price_by_product_id
            total_value_by_company_id[company.id] = total_value_by_product_id

        for product in self:
            product.total_value = sum(total_value_by_company_id[c.id].get(product.id, 0) for c in self.env.companies)
            valued_quantity = valued_quantity_by_product_id[product.id]
            product.avg_cost = product.total_value / valued_quantity if valued_quantity else std_price_by_company_id[self.env.company.id].get(product.id, product.standard_price)