def configurator_apply(
        self, *, shop_page_style_option=None, product_page_style_option=None, **kwargs
    ):
        """Override of `website` to apply eCommerce page style configurations.

        :param str shop_page_style_option: The key of the selected shop page style option. See
                                           `const.SHOP_PAGE_STYLE_MAPPING`.
        :param str product_page_style_option: The key of the selected product page style option. See
                                              `const.PRODUCT_PAGE_STYLE_MAPPING`.
        """
        res = super().configurator_apply(**kwargs)

        website = self.get_current_website()
        website_settings = {}
        category_settings = {}
        views_to_disable = []
        views_to_enable = []
        scss_customization_params = {}
        ThemeUtils = self.env['theme.utils'].with_context(website_id=website.id)
        Assets = self.env['website.assets']

        def parse_style_config(style_config_):
            website_settings.update(style_config_['website_fields'])
            category_settings.update(style_config_.get('category_fields', {}))
            views_to_disable.extend(style_config_['views']['disable'])
            views_to_enable.extend(style_config_['views']['enable'])
            scss_customization_params.update(style_config_.get('scss_customization_params', {}))

        # Extract shop page settings.
        if shop_page_style_option:
            style_config = const.SHOP_PAGE_STYLE_MAPPING[shop_page_style_option]
            parse_style_config(style_config)

        # Extract product page settings.
        if product_page_style_option:
            style_config = const.PRODUCT_PAGE_STYLE_MAPPING[product_page_style_option]
            parse_style_config(style_config)

        # Apply eCommerce page style configurations.
        if website_settings:
            website.write(website_settings)
        if category_settings:
            self.env['product.public.category'].search(website.website_domain()).write(
                category_settings
            )
        for xml_id in views_to_disable:
            ThemeUtils.disable_view(xml_id)
        for xml_id in views_to_enable:
            ThemeUtils.enable_view(xml_id)

        for footer_id in ThemeUtils._footer_templates:
            footer_view = self.with_context(website_id=website.id).viewref(
                footer_id,
                raise_if_not_found=False,  # don't raise on custom footers not installed on website
            )
            if not footer_view.active:
                continue

            footer_updated = False
            try:
                arch_tree = etree.fromstring(footer_view.arch)
            except etree.XMLSyntaxError as e:
                logger.warning("Failed to update ecommerce footer view %s: %s", footer_id, e)
            else:
                # TODO this should be moved as a website feature (not eCommerce-specific)
                footer_div_node = arch_tree.xpath(
                    "//section/div[hasclass('container') or hasclass('o_container_small') or hasclass('container-fluid')]",
                )
                # The xml view could have been modified in the backend, we don't
                # want the xpath error to break the configurator feature
                if not footer_div_node:
                    logger.warning(
                        "Failed to match footer width with header in ecommerce footer view %s",
                        footer_id,
                    )
                else:
                    # Logic for matching header width
                    if 'website.footer_copyright_content_width_fluid' in views_to_enable:
                        footer_updated = True
                        footer_div_node[0].set("class", "container-fluid s_allow_columns")
                    elif 'website.footer_copyright_content_width_small' in views_to_enable:
                        footer_updated = True
                        footer_div_node[0].set("class", "o_container_small s_allow_columns")

                if footer_id == 'website_sale.template_footer_website_sale':
                    ecommerce_categories_node = arch_tree.xpath("//t[@t-set='ecommerce_categories']")
                    if not ecommerce_categories_node:
                        logger.warning("Skipping ecommerce categories in ecommerce footer view %s", footer_id)
                    else:
                        # Logic for inserting eCommerce categories in footer
                        ecommerce_categories = self.env['product.public.category'].search([], limit=6)
                        # Deliberately hardcode categories inside the view arch, it will be transformed into
                        # static nodes after a save/edit thanks to the t-ignore in parent node.
                        footer_updated = True
                        ecommerce_categories_node[0].attrib['t-value'] = json.dumps([
                            {
                                'name': cat.name,
                                'id': cat.id,
                            }
                            for cat in ecommerce_categories
                        ])

                if footer_updated:
                    footer_view.write({'arch': etree.tostring(arch_tree)})

        if 'website_sale.template_footer_website_sale' in views_to_enable:
            scss_customization_params['footer-template'] = 'website_sale'

        # For a website editor to recognize the correct header/footer templates
        # (reason `isApplied` method of footer plugin)
        if scss_customization_params:
            Assets.make_scss_customization(
                '/website/static/src/scss/options/user_values.scss',
                scss_customization_params,
            )

        return res