def _import_retrieve_customer(self, search_plan, company, customer_values_list):
        cache = {}

        static_domain = Domain.OR([
            [*self._check_company_domain(company), ('company_id', '!=', False)],
            [('company_id', '=', False)],
        ])
        for customer_values in customer_values_list:
            partner = None
            for plan in search_plan:
                plan_values = plan(customer_values)
                if not plan_values:
                    continue

                for criteria in plan_values['criteria']:
                    domain = criteria.get('domain')
                    search_method = criteria.get('search_method')
                    if domain:
                        cache_key = str(domain)
                    else:
                        cache_key = criteria.get('cache_key')

                    # Look at the cache if the value has already been tested with this key.
                    if cache_key in cache:
                        if partner := cache[cache_key]:
                            customer_values['customer'] = partner
                            break
                        else:
                            continue

                    if domain:
                        full_domain = Domain.AND([static_domain, domain])
                        partner = self.search(
                            full_domain,
                            order='company_id, parent_id DESC, id DESC',
                            limit=1,
                        )
                    elif search_method:
                        partner = search_method({
                            **criteria,
                            'static_domain': static_domain,
                        })

                    if partner:
                        if cache_key:
                            cache[cache_key] = partner
                        customer_values['customer'] = partner
                        break

                if partner:
                    break