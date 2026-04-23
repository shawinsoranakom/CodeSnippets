def _search_display_name(self, operator, value):
        is_positive = operator not in Domain.NEGATIVE_OPERATORS
        template_domains = [[('name', operator, value)]]
        product_domains = [[('default_code', operator, value)]]

        if operator == 'in':
            product_domains.append([('barcode', 'in', value)])
            for v in value:
                if isinstance(v, str) and (m := re.search(r'(\[(.*?)\])', v)):
                    product_domains.append([('default_code', '=', m.group(2))])
        elif operator.endswith('like') and is_positive:
            product_domains.append([('barcode', 'in', [value])])

        supplier_domain = []
        if partner_id := self.env.context.get('partner_id'):
            supplier_domain = [
                ('partner_id', '=', partner_id),
                '|',
                ('product_code', operator, value),
                ('product_name', operator, value),
            ]

        # AND clauses properly hit indexes so no need for custom sql in this case.
        if operator in Domain.NEGATIVE_OPERATORS:
            domains = template_domains + product_domains
            if supplier_domain:
                domains.append([('product_tmpl_id.seller_ids', 'any', supplier_domain)])
            return Domain.AND(domains)

        # Disable active_test to simplify subqueries
        self_no_active_test = self.with_context(active_test=False)
        queries = [
            self_no_active_test._search([
                ('product_tmpl_id', 'in', self_no_active_test.env['product.template']._search(Domain.OR(template_domains)))
            ]),
            self_no_active_test._search(Domain.OR(product_domains)),
        ]
        if supplier_domain:
            queries.append(
                self_no_active_test._search([
                    (
                        'product_tmpl_id',
                        'in',
                        self_no_active_test.env['product.supplierinfo']._search(supplier_domain).subselect('product_tmpl_id'),
                    )
                ])
            )
        query = SQL(
            """(%s)""",
            SQL("UNION ALL").join(
                [SQL("(%s)", query.select()) for query in queries]
            )
        )

        return [('id', 'in', query)]