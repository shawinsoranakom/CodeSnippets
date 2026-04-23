def product(self, product, category=None, pricelist=None, **kwargs):
        if not request.website.has_ecommerce_access():
            return request.redirect(f'/web/login?redirect={request.httprequest.path}')

        if pricelist is not None:
            try:
                pricelist_id = int(pricelist)
            except ValueError:
                raise ValidationError(request.env._(
                    "Wrong format: got `pricelist=%s`, expected an integer", pricelist,
                ))
            if not self._apply_selectable_pricelist(pricelist_id):
                return request.redirect(self._get_shop_path(category))

        is_category_in_query = category and isinstance(category, str)
        category = self._validate_and_get_category(category)
        query = self._get_filtered_query_string(
            request.httprequest.query_string.decode(), keys_to_remove=['category']
        )
        # If the product doesn't belong to the category, we redirect to the canonical product URL,
        # which doesn't include the category.
        if (
            category
            and not product.filtered_domain([('public_categ_ids', 'child_of', category.id)])
        ):
            return request.redirect(f'{product._get_product_url()}?{query}', code=301)
        # If the category is provided as a query parameter (which is deprecated), we redirect to the
        # "correct" shop URL, where the category has been removed from the query parameters and
        # added to the path.
        if is_category_in_query:
            return request.redirect(
                f'{product._get_product_url(category)}?{query}', code=301
            )
        return request.render(
            'website_sale.product',
            self._prepare_product_values(
                # request context must be given to ensure context updates in overrides are correctly
                # forwarded to `_get_combination_info` call
                product.with_context(request.env.context), category, **kwargs,
            )
        )