def _process_pos_ui_product_product(self, products, config_id):

        def filter_taxes_on_company(product_taxes, taxes_by_company):
            """
            Filter the list of tax ids on a single company starting from the current one.
            If there is no tax in the result, it's filtered on the parent company and so
            on until a non empty result is found.
            """
            taxes, comp = None, self.env.company
            while not taxes and comp:
                taxes = list(set(product_taxes) & set(taxes_by_company[comp.id]))
                comp = comp.parent_id
            return taxes

        taxes = self.env['account.tax'].search(self.env['account.tax']._check_company_domain(self.env.company))
        # group all taxes by company in a dict where:
        # - key: ID of the company
        # - values: list of tax ids
        taxes_by_company = defaultdict(set)
        if self.env.company.parent_id:
            for tax in taxes:
                taxes_by_company[tax.company_id.id].add(tax.id)

        different_currency = {}
        for product in products:
            currency_id = product['currency_id']
            if currency_id != config_id.currency_id.id:
                different_currency.setdefault(currency_id, []).append(product)

        self._add_archived_combinations(products)
        for currency_id, product_templates in different_currency.items():
            currency = self.env['res.currency'].browse(currency_id)
            for product in product_templates:
                product['list_price'] = currency._convert(product['list_price'], config_id.currency_id, self.env.company, fields.Date.today())
                product['standard_price'] = currency._convert(product['standard_price'], config_id.currency_id, self.env.company, fields.Date.today())

        for product in products:
            product['image_128'] = bool(product['image_128'])

            if len(taxes_by_company) > 1 and len(product['taxes_id']) > 1:
                product['taxes_id'] = filter_taxes_on_company(product['taxes_id'], taxes_by_company)