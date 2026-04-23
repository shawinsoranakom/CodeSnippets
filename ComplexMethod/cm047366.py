def button_install(self):
        company_countries = self.env['res.company'].search([]).country_id
        # domain to select auto-installable (but not yet installed) modules
        auto_domain = [('state', '=', 'uninstalled'), ('auto_install', '=', True)]

        # determine whether an auto-install module must be installed:
        #  - all its dependencies are installed or to be installed,
        #  - at least one dependency is 'to install'
        #  - if the module is country specific, at least one company is in one of the countries
        install_states = frozenset(('installed', 'to install', 'to upgrade'))
        def must_install(module):
            states = {dep.state for dep in module.dependencies_id if dep.auto_install_required}
            return states <= install_states and 'to install' in states and (
                not module.country_ids or module.country_ids & company_countries
            )

        modules = self
        while modules:
            # Mark the given modules and their dependencies to be installed.
            modules._state_update('to install', ['uninstalled'])

            # Determine which auto-installable modules must be installed.

            if config.get('skip_auto_install'):
                modules = None
            else:
                modules = self.search(auto_domain).filtered(must_install)

        # the modules that are installed/to install/to upgrade
        install_mods = self.search([('state', 'in', list(install_states))])

        # check individual exclusions
        install_names = {module.name for module in install_mods}
        for module in install_mods:
            for exclusion in module.exclusion_ids:
                if exclusion.name in install_names:
                    raise UserError(_(
                        'Modules "%(module)s" and "%(incompatible_module)s" are incompatible.',
                        module=module.shortdesc,
                        incompatible_module=exclusion.exclusion_id.shortdesc,
                    ))

        # check category exclusions
        def closure(module):
            todo = result = module
            while todo:
                result |= todo
                todo = todo.dependencies_id.depend_id
            return result

        exclusives = self.env['ir.module.category'].search([('exclusive', '=', True)])
        for category in exclusives:
            # retrieve installed modules in category and sub-categories
            categories = category.search([('id', 'child_of', category.ids)])
            modules = install_mods.filtered(lambda mod: mod.category_id in categories)
            # the installation is valid if all installed modules in categories
            # belong to the transitive dependencies of one of them
            if modules and not any(modules <= closure(module) for module in modules):
                labels = dict(self.fields_get(['state'])['state']['selection'])
                raise UserError(
                    _('You are trying to install incompatible modules in category "%(category)s":%(module_list)s', category=category.name, module_list=''.join(
                        f"\n- {module.shortdesc} ({labels[module.state]})"
                        for module in modules
                    ))
                )

        return dict(ACTION_DICT, name=_('Install'))