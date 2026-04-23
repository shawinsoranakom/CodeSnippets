def button_upgrade(self):
        if not self:
            return
        Dependency = self.env['ir.module.module.dependency']
        self.update_list()

        todo = list(self)
        if 'base' in self.mapped('name'):
            # If an installed module is only present in the dependency graph through
            # a new, uninstalled dependency, it will not have been selected yet.
            # An update of 'base' should also update these modules, and as a consequence,
            # install the new dependency.
            todo.extend(self.search([
                ('state', '=', 'installed'),
                ('name', '!=', 'studio_customization'),
                ('id', 'not in', self.ids),
            ]))
        i = 0
        while i < len(todo):
            module = todo[i]
            i += 1
            if module.state not in ('installed', 'to upgrade'):
                raise UserError(_("Cannot upgrade module “%s”. It is not installed.", module.name))
            if self.get_module_info(module.name).get("installable", True):
                self.check_external_dependencies(module.name, 'to upgrade')
            for dep in Dependency.search([('name', '=', module.name)]):
                if (
                    dep.module_id.state == 'installed'
                    and dep.module_id not in todo
                    and dep.module_id.name != 'studio_customization'
                ):
                    todo.append(dep.module_id)

        self.browse(module.id for module in todo).write({'state': 'to upgrade'})

        to_install = []
        for module in todo:
            if not self.get_module_info(module.name).get("installable", True):
                continue
            for dep in module.dependencies_id:
                if dep.state == 'unknown':
                    raise UserError(_('You try to upgrade the module %(module)s that depends on the module: %(dependency)s.\nBut this module is not available in your system.', module=module.name, dependency=dep.name))
                if dep.state == 'uninstalled':
                    to_install += self.search([('name', '=', dep.name)]).ids

        self.browse(to_install).button_install()
        return dict(ACTION_DICT, name=_('Apply Schedule Upgrade'))