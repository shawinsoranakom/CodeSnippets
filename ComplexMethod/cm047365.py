def _state_update(self, newstate, states_to_update, level=100):
        if level < 1:
            raise UserError(_('Recursion error in modules dependencies!'))

        for module in self:
            if module.state not in states_to_update:
                continue

            # determine dependency modules to update/others
            update_mods, ready_mods = self.browse(), self.browse()
            for dep in module.dependencies_id:
                if dep.state == 'unknown':
                    raise UserError(_(
                        'You try to install module "%(module)s" that depends on module "%(dependency)s".\nBut the latter module is not available in your system.',
                        module=module.name, dependency=dep.name,
                    ))
                if dep.depend_id.state == newstate:
                    ready_mods += dep.depend_id
                else:
                    update_mods += dep.depend_id

            # update dependency modules that require it
            update_mods._state_update(newstate, states_to_update, level=level-1)

            if module.state in states_to_update:
                # check dependencies and update module itself
                self.check_external_dependencies(module.name, newstate)
                module.write({'state': newstate})