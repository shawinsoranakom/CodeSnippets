def _change_website_config(self, **options):
        if not request.env.user.has_group('website.group_website_restricted_editor'):
            raise NotFound()

        current_website = request.env['website'].get_current_website()
        # Restrict options we can write to.
        writable_fields = {
            'shop_page_container', 'shop_ppg', 'shop_ppr', 'shop_default_sort', 'shop_gap',
            'shop_opt_products_design_classes', 'product_page_container',
            'product_page_image_layout', 'product_page_image_width', 'product_page_grid_columns',
            'product_page_image_spacing', 'product_page_image_ratio',
            'product_page_image_ratio_mobile', 'product_page_cols_order',
            'product_page_image_roundness', 'product_page_cta_design'
        }
        # Default ppg to 1.
        if 'ppg' in options and not options['ppg']:
            options['ppg'] = 1
        if 'product_page_grid_columns' in options:
            options['product_page_grid_columns'] = int(options['product_page_grid_columns'])

        # Checkout Extra Step
        if 'extra_step' in options:
            extra_step_view = current_website.viewref('website_sale.extra_info')
            extra_step = current_website._get_checkout_step('/shop/extra_info')
            extra_step_view.active = extra_step.is_published = options.get('extra_step') == 'true'

        write_vals = {k: v for k, v in options.items() if k in writable_fields}
        if write_vals:
            current_website.write(write_vals)