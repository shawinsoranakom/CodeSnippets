def _prepare_values(self, limit=None, search_domain=None, **kwargs):
        website = self.env['website'].get_current_website()
        if (
            (self.model_name or kwargs.get('res_model')) in ('product.product', 'product.public.category')
            and not website.has_ecommerce_access()
        ):
            return []
        hide_variants = False
        if search_domain and 'hide_variants' in search_domain:
            hide_variants = True
            search_domain.remove('hide_variants')
        update_limit_cache = False
        product_limit = limit or self.limit
        if hide_variants and self.filter_id.model_id == 'product.product':
            # When hiding variants, temporarily update cache to increase `self.limit`
            # so we hopefully end up with the correct amount of product templates
            update_limit_cache = partial(
                self.env.cache.set,
                record=self,
                field=self._fields['limit'],
            )
            limit = product_limit ** 2  # heuristic, may still be inadequate in some cases
            stored_limit = self.limit
            update_limit_cache(value=limit)
        res = super(
            WebsiteSnippetFilter,
            self.with_context(hide_variants=hide_variants, product_limit=product_limit),
        )._prepare_values(limit=limit, search_domain=search_domain, **kwargs)
        if update_limit_cache:
            update_limit_cache(value=stored_limit)
        return res