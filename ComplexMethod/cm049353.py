def _search_get_detail(self, website, order, options):
        with_image = options['displayImage']
        with_description = options['displayDescription']
        with_category = options['displayExtraLink']
        with_price = options['displayDetail']
        domains = [website.sale_product_domain()]
        category = options.get('category')
        tags = options.get('tags')
        min_price = options.get('min_price')
        max_price = options.get('max_price')
        attribute_value_dict = options.get('attribute_value_dict')
        if category:
            domains.append([('public_categ_ids', 'child_of', self.env['ir.http']._unslug(category)[1])])
        if tags:
            if isinstance(tags, str):
                tags = tags.split(',')
            tags = list(map(int, tags))  # Convert list of strings to list of integers
            domains.append(Domain.OR([
                Domain('product_tag_ids', 'in', tags),
                Domain('product_variant_ids.additional_product_tag_ids', 'in', tags),
            ]))
        if min_price:
            domains.append([('list_price', '>=', min_price)])
        if max_price:
            domains.append([('list_price', '<=', max_price)])
        if attribute_value_dict:
            domains.extend(self._get_attribute_value_domain(attribute_value_dict))
        search_fields = ['name', 'default_code', 'variants_default_code']
        fetch_fields = ['id', 'name', 'website_url']
        mapping = {
            'name': {'name': 'name', 'type': 'text', 'match': True},
            'default_code': {'name': 'default_code', 'type': 'text', 'match': True},
            'product_variant_ids.default_code': {'name': 'product_variant_ids.default_code', 'type': 'text', 'match': True},
            'website_url': {'name': 'website_url', 'type': 'text', 'truncate': False},
        }
        if with_image:
            mapping['image_url'] = {'name': 'image_url', 'type': 'html'}
        if with_description:
            # Internal note is not part of the rendering.
            search_fields.append('description')
            fetch_fields.append('description')
            search_fields.append('description_sale')
            fetch_fields.append('description_sale')
            mapping['description'] = {'name': 'description_sale', 'type': 'text', 'match': True}
        if with_price:
            mapping['detail'] = {'name': 'price', 'type': 'html', 'display_currency': options['display_currency']}
            mapping['detail_strike'] = {'name': 'list_price', 'type': 'html', 'display_currency': options['display_currency']}
        if with_category:
            mapping['extra_link'] = {'name': 'category', 'type': 'html'}
        return {
            'model': 'product.template',
            'base_domain': domains,
            'search_fields': search_fields,
            'fetch_fields': fetch_fields,
            'mapping': mapping,
            'icon': 'fa-shopping-cart',
        }