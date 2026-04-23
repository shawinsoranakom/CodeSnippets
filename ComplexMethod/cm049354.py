def _search_render_results(self, fetch_fields, mapping, icon, limit):
        with_image = 'image_url' in mapping
        with_category = 'extra_link' in mapping
        with_price = 'detail' in mapping
        results_data = super()._search_render_results(fetch_fields, mapping, icon, limit)
        current_website = self.env['website'].get_current_website()
        for product, data in zip(self, results_data):
            categ_ids = product.public_categ_ids.filtered(lambda c: not c.website_id or c.website_id == current_website)
            if with_price:
                combination_info = product._get_combination_info(only_template=True)
                data['price'], list_price = self._search_render_results_prices(
                    mapping, combination_info
                )
                if list_price:
                    data['list_price'] = list_price

            if with_image:
                data['image_url'] = '/web/image/product.template/%s/image_128' % data['id']
            if with_category and categ_ids:
                data['category'] = self.env['ir.ui.view'].sudo()._render_template(
                    "website_sale.product_category_extra_link",
                    {
                        'categories': categ_ids,
                        'slug': self.env['ir.http']._slug,
                        'shop_path': SHOP_PATH,
                    }
                )
        return results_data