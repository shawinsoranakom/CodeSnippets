def _get_product_url(self, category=None, query_params=None, grouped_attributes_values=None):
        self.ensure_one()
        slug = self.env['ir.http']._slug

        url = (category and f'/shop/{slug(category)}/{slug(self)}') or self.website_url

        query_params = query_params or {}
        if grouped_attributes_values:
            product_grouped_values = self.attribute_line_ids.value_ids.grouped('attribute_id')
            available_pav_ids = [
                next(v.id for v in pavs if v in product_grouped_values[pa])
                for pa, pavs in grouped_attributes_values.items()
                if pa in product_grouped_values
            ]
            available_pav_ids.sort()
            query_params['attribute_values'] = ','.join(str(i) for i in available_pav_ids)

        if query_params:
            url = f'{url}?{urls.url_encode(query_params)}'

        return url