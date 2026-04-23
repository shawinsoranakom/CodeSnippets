def _preconfigure_snippet(self, snippet, el, customizations):
        """Apply default configuration values to a snippet element.

        This ensures that when a dynamic snippet is appended via the
        configurator, all of its required default classes/attributes
        are added to the DOM element before it is rendered.
        """
        def modify_class(target_classes, class_name, operation):
            """Add or remove a single class string from target_classes list."""
            if operation == 'remove' and class_name in target_classes:
                target_classes.remove(class_name)
            elif operation == 'add' and class_name not in target_classes:
                target_classes.append(class_name)

        default_settings = self._get_snippet_defaults(snippet)
        if not (customizations or default_settings):
            # Nothing to preconfigure on the given snippet
            return

        snippet_classes = el.get('class', '').split()

        filter_name = customizations.get('filter_xmlid') or default_settings.get('filter_xmlid')
        if filter_name:
            selected_filter = self.env.ref(filter_name)
            el.set('data-filter-id', str(selected_filter.id))
            el.set('data-number-of-records', str(selected_filter.limit))

        selected_template_key = customizations.get('template_key') or default_settings.get('template_key')
        if selected_template_key:
            el.set('data-template-key', selected_template_key)
            template_class = re.sub(r'.*\.dynamic_filter_template_', 's_', selected_template_key)
            if template_class not in snippet_classes:
                snippet_classes.append(template_class)

        # Add 'o_colored_level' to maintain correct color configuration.
        snippet_classes.append('o_colored_level')

        # Apply class modifications (add/remove) to the snippet or its children.
        # - If dict is found, apply to the first child matching the selector.
        # - Otherwise, treated as direct modification on the snippet element.
        class_modifications = [
            ('remove', customizations.get('remove_classes', []) or default_settings.get('remove_classes', [])),
            ('add', customizations.get('add_classes', []) or default_settings.get('add_classes', [])),
        ]

        for operation, items in class_modifications:
            for item in items:
                if isinstance(item, dict):
                    for selector, classes in item.items():
                        child_el = el.xpath(f"//*[hasclass('{selector}')]")
                        if child_el:
                            node = child_el[0]
                            child_classes = node.get('class', '').split()
                            modify_class(child_classes, classes, operation)
                            node.set('class', ' '.join(child_classes))
                else:
                    modify_class(snippet_classes, item, operation)

        data_attributes = {
            **default_settings.get('data_attributes', {}),
            **customizations.get('data_attributes', {}),
        }
        for key, value in data_attributes.items():
            el.set(f'data-{key}', value)

        el.set('class', ' '.join(snippet_classes))

        style = customizations.get('style', {}) or default_settings.get('style', {})
        if style:
            style_attr = ' '.join(f'{attr}: {value};' for attr, value in style.items())
            el.set('style', style_attr)

        # Apply theme-specific customizations to the dynamic snippets
        if 'background' in customizations:
            self._set_background_options(el, customizations['background'])

        return