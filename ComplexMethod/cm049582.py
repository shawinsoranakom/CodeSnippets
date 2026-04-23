def update_footer_template(self, template_key, possible_values):
        """ Enables the footer template and its corresponding copyright template
            on template change. The goal is to ensure that the content width of
            the copyright aligns with the footer.
        """

        # Define templates views to enable/disable
        views_enable = [template_key]
        views_disable = self.theme_customize_data_get(possible_values, is_view_data=True)

        # Define the possible footer classes and corresponding views
        width_views = {
            'container-fluid': 'website.footer_copyright_content_width_fluid',
            'o_container_small': 'website.footer_copyright_content_width_small',
        }

        # Parse new footer template and get the content width
        new_template = self._get_customize_data([template_key], is_view_data=True)
        if not new_template or not new_template[0].arch:
            return

        tree = etree.HTML(new_template[0].arch)
        container_classes = ['container', 'container-fluid', 'o_container_small']
        classes_selector = ' or '.join([f"hasclass('{c}')" for c in container_classes])
        res = tree.xpath(f"//div[{classes_selector}]")

        # Define copyright views to enable/disable
        if res:
            classes = res[0].get('class').split()
            width = next((c for c in container_classes if c in classes), False)
            if width:
                view = width_views.get(width)
                if view is not None:
                    views_enable += [view]
                views_disable += [v for k, v in width_views.items() if k != width]

        # Activate/Deactivate the computed views
        self.theme_customize_data(is_view_data=True,
                                  enable=views_enable,
                                  disable=views_disable,
                                  reset_view_arch=False)