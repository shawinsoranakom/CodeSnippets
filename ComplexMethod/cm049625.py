def _generate_primary_snippet_templates(self):
        """ Generates snippet templates hierarchy based on manifest entries for
            use in the configurator and when creating new pages from templates.
        """
        def split_key(snippet_key):
            """ Snippets xmlid can be written without the module part, meaning
                it is a shortcut for a website module snippet.

                :param snippet_key: xmlid with or without the module part
                    'website' is assumed to be the default module
                :return: module and key extracted from the snippet_key
            """
            return snippet_key.split('.') if '.' in snippet_key else ('website', snippet_key)

        def create_missing_views(create_values):
            """ Creates the snippet primary view records that do not exist yet.

                :param create_values: values of records to create
                :return: number of created records
            """
            # Defensive code (low effort): `if values` should always be set
            create_values = [values for values in create_values if values]

            keys = [values['key'] for values in create_values]
            existing_primary_template_keys = self.env['ir.ui.view'].with_context(active_test=False).search_fetch([
                ('mode', '=', 'primary'), ('key', 'in', keys),
            ], ['key']).mapped('key')
            missing_create_values = [values for values in create_values if values['key'] not in existing_primary_template_keys]
            missing_records = self.env['ir.ui.view'].with_context(no_cow=True).create(missing_create_values)
            self._create_model_data(missing_records)
            return len(missing_records)

        def get_create_vals(name, snippet_key, parent_wrap, new_wrap):
            """ Returns the create values for the new primary template of the
                snippet having snippet_key as its base key, having a new key
                formatted with new_wrap, and extending a parent with the key
                formatted with parent_wrap.

                :param name: name
                :param snippet_key: xmlid of the base block
                :param parent_wrap: string pattern used to format the
                    snippet_key's second part to reach the parent key
                :param new_wrap: string pattern used to format the
                    snippet_key's second part to reach the new key
                :return: create values for the new record
            """
            module, xmlid = split_key(snippet_key)
            parent_key = f'{module}.{parent_wrap % xmlid}'
            # Equivalent to using an already cached ref, without failing on
            # missing key - because the parent records have just been created.
            parent_id = self.env['ir.model.data']._xmlid_to_res_model_res_id(parent_key, False)
            if not parent_id:
                _logger.warning("No such snippet template: %r", parent_key)
                return None
            return {
                'name': name,
                'key': f'{module}.{new_wrap % xmlid}',
                'inherit_id': parent_id[1],
                'mode': 'primary',
                'type': 'qweb',
                'arch': '<t/>',
            }

        def get_distinct_snippet_names(structure):
            """ Returns the distinct leaves of the structure (tree leaf's list
                elements).

                :param structure: dict or list or snippet names
                :return: distinct snippet names
            """
            items = []
            for value in structure.values():
                if isinstance(value, list):
                    items.extend(value)
                else:
                    items.extend(get_distinct_snippet_names(value))
            return set(items)

        create_count = 0
        manifest = Manifest.for_addon(self.name)

        # ------------------------------------------------------------
        # Configurator
        # ------------------------------------------------------------

        configurator_snippets = dict(manifest.get('configurator_snippets', {}))
        addons = manifest.get('configurator_snippets_addons', {})
        installed_modules = self.env['ir.module.module']._installed()

        # Add addon snippets to the main snippet list for batch generation
        for module_name, pages in addons.items():
            # generate snippet only if the module is installed
            if module_name not in installed_modules and module_name != self.name:
                continue
            for page, snippets_to_insert in pages.items():
                snippets = configurator_snippets.setdefault(page, [])
                dynamic_snippets = [snippet for snippet, *_ in snippets_to_insert]
                configurator_snippets[page] = list(dict.fromkeys(snippets + dynamic_snippets))

        # Generate general configurator snippet templates
        create_values = []
        # Every distinct snippet name across all configurator pages.
        for snippet_name in get_distinct_snippet_names(configurator_snippets):
            create_values.append(get_create_vals(
                f"Snippet {snippet_name!r} for pages generated by the configurator",
                snippet_name, '%s', 'configurator_%s'
            ))
        create_count += create_missing_views(create_values)

        # Generate configurator snippet templates for specific pages
        create_values = []
        for page_name in configurator_snippets:
            for snippet_name in set(configurator_snippets[page_name]):
                create_values.append(get_create_vals(
                    f"Snippet {snippet_name!r} for {page_name!r} pages generated by the configurator",
                    snippet_name, 'configurator_%s', f'configurator_{page_name}_%s'
                ))
        create_count += create_missing_views(create_values)

        # ------------------------------------------------------------
        # New page templates
        # ------------------------------------------------------------

        templates = manifest.get('new_page_templates', {})

        # Generate general new page snippet templates
        create_values = []
        # Every distinct snippet name across all new page templates.
        for snippet_name in get_distinct_snippet_names(templates):
            create_values.append(get_create_vals(
                f"Snippet {snippet_name!r} for new page templates",
                snippet_name, '%s', 'new_page_template_%s'
            ))
        create_count += create_missing_views(create_values)

        # Generate new page snippet templates for new page template groups
        create_values = []
        for group in templates:
            # Every distinct snippet name across all new page templates of group.
            for snippet_name in get_distinct_snippet_names(templates[group]):
                create_values.append(get_create_vals(
                    f"Snippet {snippet_name!r} for new page {group!r} templates",
                    snippet_name, 'new_page_template_%s', f'new_page_template_{group}_%s'
                ))
        create_count += create_missing_views(create_values)

        # Generate new page snippet templates for specific new page templates within groups
        create_values = []
        for group in templates:
            for template_name in templates[group]:
                for snippet_name in templates[group][template_name]:
                    create_values.append(get_create_vals(
                        f"Snippet {snippet_name!r} for new page {group!r} template {template_name!r}",
                        snippet_name, f'new_page_template_{group}_%s', f'new_page_template_{group}_{template_name}_%s'
                    ))
        create_count += create_missing_views(create_values)

        if create_count:
            _logger.info("Generated %s primary snippet templates for %r", create_count, self.name)