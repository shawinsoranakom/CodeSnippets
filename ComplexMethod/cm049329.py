def _prepare_product_values(self, product, category, **kwargs):
        ProductCategory = request.env['product.public.category']
        product_markup_data = [product._to_markup_data(request.website)]
        original_category = category
        category = category or product.public_categ_ids.filtered(
            lambda c: c.can_access_from_current_website()
        )[:1]
        if category:
            # Add breadcrumb's SEO data.
            product_markup_data.append(self._prepare_breadcrumb_markup_data(
                request.website.get_base_url(), category, product.name
            ))

        if (last_attributes_search := request.session.get('attribute_values', [])):
            keep = QueryURL(
                self._get_shop_path(original_category),
                attribute_values=last_attributes_search
            )
        else:
            keep = QueryURL(self._get_shop_path(original_category))

        if attribute_values := kwargs.get('attribute_values', ''):
            attribute_value_ids = {int(i) for i in attribute_values.split(',')}
            combination = product.attribute_line_ids.mapped(
                lambda ptal: (
                    ptal.product_template_value_ids.filtered(
                        lambda ptav: (
                            ptav.ptav_active
                            and ptav.product_attribute_value_id.id in attribute_value_ids
                        )
                    )[:1]
                ) or ptal.product_template_value_ids.filtered('ptav_active')[:1]
            )
            combination_info = product._get_combination_info(
                combination=request.env['product.template.attribute.value'].concat(combination)
            )
        else:
            combination_info = product._get_combination_info()

        # Needed to trigger the recently viewed product rpc
        view_track = request.website.viewref("website_sale.product").track

        return {
            'categories': ProductCategory.search([('parent_id', '=', False)]),
            'category': category,
            'original_category': original_category,
            'combination_info': combination_info,
            'keep': keep,
            'main_object': product,
            'product': product,
            'product_variant': request.env['product.product'].browse(combination_info['product_id']),
            'view_track': view_track,
            'product_markup_data': json_scriptsafe.dumps(product_markup_data, indent=2),
            'shop_path': SHOP_PATH,
        }