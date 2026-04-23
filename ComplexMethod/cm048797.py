def _import_retrieve_tax(self, search_plan, company, tax_values_list):
        cache = {}

        static_domain = Domain.OR([
            [*self._check_company_domain(company), ('company_id', '!=', False)],
            [('company_id', '=', False)],
        ])
        for tax_values in tax_values_list:
            tax_domain = [
               ('amount_type', '=', tax_values['amount_type']),
               ('type_tax_use', '=', tax_values['type_tax_use']),
               ('amount', '=', tax_values['amount']),
            ]
            orders = ['sequence', 'id']
            if name := tax_values.get('name'):
                tax_domain.append(('name', '=', name))
            if tax_exigibility := tax_values.get('tax_exigibility'):
                tax_domain.append(('tax_exigibility', '=', tax_exigibility))
            if (
                (ubl_cii_tax_category_code := tax_values.get('ubl_cii_tax_category_code'))
                and 'ubl_cii_tax_category_code' in self._fields
            ):
                tax_domain.append(('ubl_cii_tax_category_code', 'in', (ubl_cii_tax_category_code, False)))
                orders.insert(0, 'ubl_cii_tax_category_code')

            for plan in search_plan:
                tax = None
                plan_values = plan(tax_values)
                if not plan_values:
                    continue

                for criteria in plan_values['criteria']:
                    domain = criteria.get('domain')
                    search_method = criteria.get('search_method')
                    if domain:
                        domain = Domain.AND([tax_domain, domain])
                        cache_key = str(domain)
                    else:
                        cache_key = criteria.get('cache_key')

                    # Look at the cache if the value has already been tested with this key.
                    if cache_key in cache:
                        if tax := cache[cache_key]:
                            tax_values['tax'] = tax
                            break
                        else:
                            continue

                    if domain:
                        full_domain = Domain.AND([static_domain, domain])
                        tax = self.search(full_domain, order=','.join(orders), limit=1)
                    elif search_method:
                        tax = search_method({
                            **criteria,
                            'static_domain': Domain.AND([tax_domain, static_domain]),
                        })

                    if tax:
                        if cache_key:
                            cache[cache_key] = tax
                        tax_values['tax'] = tax
                        break

                if tax:
                    break