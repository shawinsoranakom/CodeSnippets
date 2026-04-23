def _compute_tax_ids(self):
        lines_by_company = defaultdict(lambda: self.env['sale.order.line'])
        cached_taxes = {}
        for line in self:
            if line.product_type == 'combo':
                line.tax_ids = False
                continue
            lines_by_company[line.company_id] += line
        for company, lines in lines_by_company.items():
            for line in lines.with_company(company):
                taxes = None
                if line.product_id:
                    taxes = line.product_id.taxes_id._filter_taxes_by_company(company)
                if not line.product_id or not taxes:
                    # Nothing to map
                    line.tax_ids = False
                    continue
                fiscal_position = line.order_id.fiscal_position_id
                cache_key = (fiscal_position.id, company.id, tuple(taxes.ids))
                cache_key += line._get_custom_compute_tax_cache_key()
                if cache_key in cached_taxes:
                    result = cached_taxes[cache_key]
                else:
                    result = fiscal_position.map_tax(taxes)
                    cached_taxes[cache_key] = result
                # If company_id is set, always filter taxes by the company
                line.tax_ids = result