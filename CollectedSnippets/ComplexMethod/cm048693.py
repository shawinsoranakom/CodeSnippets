def _import_retrieve_product(self, search_plan, company, product_values_list):
        cache = {}

        static_domain = Domain.OR([
            [*self._check_company_domain(company), ('company_id', '!=', False)],
            [('company_id', '=', False)],
        ])
        for product_values in product_values_list:
            product = None
            for plan in search_plan:
                plan_values = plan(product_values)
                if not plan_values:
                    continue

                for criteria in plan_values['criteria']:
                    domain = criteria.get('domain')
                    search_method = criteria.get('search_method')
                    if domain:
                        domain = list(domain)
                        cache_key = str(domain)
                    else:
                        cache_key = criteria.get('cache_key')

                    cache_key = frozendict({
                        'cache_key': cache_key,
                        'intrastat_code': product_values.get('intrastat_code'),
                        'unspsc_code': product_values.get('unspsc_code'),
                        'l10n_ro_cpv_code': product_values.get('l10n_ro_cpv_code'),
                        'cg_item_classification_code': product_values.get('cg_item_classification_code'),
                    })

                    # Look at the cache if the value has already been tested with this key.
                    if cache_key in cache:
                        if product := cache[cache_key]:
                            product_values['product'] = product
                            break
                        else:
                            continue

                    orders = ['company_id', 'id DESC']
                    product_extra_domain = []
                    if (
                        (intrastat_code := product_values.get('intrastat_code'))
                        and 'intrastat_code_id' in self._fields
                        and (intrastat_code_record := self.env['account.intrastat.code'].search([('code', '=', intrastat_code)], limit=1))
                    ):
                        product_extra_domain.append(('intrastat_code_id', 'in', (intrastat_code_record.id, False)))
                        orders.insert(1, 'intrastat_code_id')
                    if (
                        (unspsc_code := product_values.get('unspsc_code'))
                        and 'unspsc_code_id' in self._fields
                        and (unspsc_code_record := self.env['product.unspsc.code'].search([('code', '=', unspsc_code)], limit=1))
                    ):
                        product_extra_domain.append(('unspsc_code_id', 'in', (unspsc_code_record.id, False)))
                        orders.insert(1, 'unspsc_code_id')
                    if (
                        (l10n_ro_cpv_code := product_values.get('l10n_ro_cpv_code'))
                        and 'cpv_code_id' in self._fields
                        and (cpv_code_record := self.env['l10n_ro.cpv.code'].search([('code', '=', l10n_ro_cpv_code)], limit=1))
                    ):
                        product_extra_domain.append(('cpv_code_id', 'in', (cpv_code_record.id, False)))
                        orders.insert(1, 'cpv_code_id')
                    if (
                        (cg_item_classification_code := product_values.get('cg_item_classification_code'))
                        and 'l10n_hr_kpd_category_id' in self._fields
                        and (cpv_code_record := self.env['l10n_hr.kpd.category'].search([('name', '=', cg_item_classification_code)], limit=1))
                    ):
                        product_extra_domain.append(('l10n_hr_kpd_category_id', 'in', (cpv_code_record.id, False)))
                        orders.insert(1, 'l10n_hr_kpd_category_id')

                    product_domain = Domain.AND([
                        static_domain,
                        product_extra_domain
                    ])

                    if domain:
                        full_domain = Domain.AND([product_domain, domain])
                        product = self.search(
                            full_domain,
                            order=', '.join(orders),
                            limit=1,
                        )
                    elif search_method:
                        product = search_method({
                            **criteria,
                            'static_domain': product_domain,
                        })

                    if product:
                        if cache_key:
                            cache[cache_key] = product
                        product_values['product'] = product
                        break

                if product:
                    break