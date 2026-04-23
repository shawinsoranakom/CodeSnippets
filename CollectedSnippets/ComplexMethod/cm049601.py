def get_theme_configurator_snippets(self, theme_name):
        """
        Prepare and return configurator_snippets by fetching theme snippets and
        inserting addon snippets at their intended positions.
        """
        configurator_snippets = {
            **get_manifest('website')['configurator_snippets'],
            **get_manifest(theme_name).get('configurator_snippets', {}),
        }
        configurator_snippets_addons = {
            **get_manifest(theme_name).get('configurator_snippets_addons', {}),
        }

        if not configurator_snippets_addons:
            return configurator_snippets

        installed_modules = self.env['ir.module.module']._installed()

        for module_name, module_addon in configurator_snippets_addons.items():
            if module_name not in installed_modules:
                continue
            for page, snippets_to_insert in module_addon.items():
                snippet_list = configurator_snippets.setdefault(page, [])
                for snippet_name, position, target in snippets_to_insert:
                    if snippet_name in snippet_list:
                        continue
                    try:
                        snippet_idx = snippet_list.index(target) + (position == 'after')
                        snippet_list.insert(snippet_idx, snippet_name)
                    except ValueError:
                        logger.error(
                            "Skipping snippet '%s' because the target snippet is misconfigured.",
                            snippet_name,
                        )

        return configurator_snippets