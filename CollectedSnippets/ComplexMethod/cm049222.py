def name_search(self, name='', domain=None, operator='ilike', limit=100):
        if not name:
            return super().name_search(name, domain, operator, limit)
        # search progressively by the most specific attributes
        positive_operators = ['=', 'ilike', '=ilike', 'like', '=like']
        is_positive = not operator in Domain.NEGATIVE_OPERATORS
        products = self.browse()
        domain = Domain(domain or Domain.TRUE)
        if operator in positive_operators:
            products = self.search_fetch(domain & Domain('default_code', '=', name), ['display_name'], limit=limit) \
                or self.search_fetch(domain & Domain('barcode', '=', name), ['display_name'], limit=limit)
        if not products:
            if is_positive:
                # Do not merge the 2 next lines into one single search, SQL search performance would be abysmal
                # on a database with thousands of matching products, due to the huge merge+unique needed for the
                # OR operator (and given the fact that the 'name' lookup results come from the ir.translation table
                # Performing a quick memory merge of ids in Python will give much better performance
                products = self.search_fetch(domain & Domain('default_code', operator, name), ['display_name'], limit=limit)
                limit_rest = limit and limit - len(products)
                if limit_rest is None or limit_rest > 0:
                    products_query = self._search(domain & Domain('default_code', operator, name), limit=limit)
                    products |= self.search_fetch(domain & Domain('id', 'not in', products_query) & Domain('name', operator, name), ['display_name'], limit=limit_rest)
            else:
                domain_neg = Domain('name', operator, name) & (
                    Domain('default_code', operator, name) | Domain('default_code', '=', False)
                )
                products = self.search_fetch(domain & domain_neg, ['display_name'], limit=limit)
        if not products and operator in positive_operators and (m := re.search(r'(\[(.*?)\])', name)):
            match_domain = Domain('default_code', '=', m.group(2))
            products = self.search_fetch(domain & match_domain, ['display_name'], limit=limit)
        if not products and (partner_id := self.env.context.get('partner_id')):
            # still no results, partner in context: search on supplier info as last hope to find something
            supplier_domain = Domain([
                ('partner_id', '=', partner_id),
                '|',
                ('product_code', operator, name),
                ('product_name', operator, name),
            ])
            match_domain = Domain('product_tmpl_id.seller_ids', 'any', supplier_domain)
            products = self.search_fetch(domain & match_domain, ['display_name'], limit=limit)
        return [(product.id, product.display_name) for product in products.sudo()]