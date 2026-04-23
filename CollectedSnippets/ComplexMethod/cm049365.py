def _get_products_latest_viewed(self, website, limit, domain, **kwargs):
        products = self.env['product.product']
        visitor = self.env['website.visitor']._get_visitor_from_request()
        if visitor:
            excluded_products = request.cart.order_line.product_id.ids
            tracked_products = self.env['website.track'].sudo()._read_group([
                ('visitor_id', '=', visitor.id),
                ('product_id', '!=', False),
                ('product_id.website_published', '=', True),
                ('product_id', 'not in', excluded_products),
            ], ['product_id'], limit=limit, order='visit_datetime:max DESC')
            if self.env.context.get('hide_variants'):
                product_ids = [
                    product.product_tmpl_id.product_variant_id.id
                    for [product] in tracked_products
                ]
            else:
                product_ids = [product.id for [product] in tracked_products]
            if product_ids:
                domain = Domain(domain) & Domain('id', 'in', product_ids)
                filtered_ids = set(self.env['product.product']._search(domain, limit=limit))
                # `search` will not keep the order of tracked products; however, we want to keep
                # that order (latest viewed first).
                products = self.env['product.product'].with_context(
                    display_default_code=False, add2cart_rerender=True,
                ).browse([product_id for product_id in product_ids if product_id in filtered_ids])

        return products