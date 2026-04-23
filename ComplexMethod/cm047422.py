def execute(self):
        """
        Called when settings are saved.

        This method will call `set_values` and will install/uninstall any modules defined by
        `module_` Boolean fields and then trigger a web client reload.

        .. warning::

            This method **SHOULD NOT** be overridden, in most cases what you want to override is
            `~set_values()` since `~execute()` does little more than simply call `~set_values()`.

            The part that installs/uninstalls modules **MUST ALWAYS** be at the end of the
            transaction, otherwise there's a big risk of registry <-> database desynchronisation.
        """
        self.ensure_one()
        if not self.env.is_admin():
            raise AccessError(_("Only administrators can change the settings"))

        self = self.with_context(active_test=False)
        classified = self._get_classified_fields()

        self.set_values()

        # module fields: install/uninstall the selected modules
        to_install = classified['module'].filtered(
            lambda m: self[f'module_{m.name}'] and m.state != 'installed')
        to_uninstall = classified['module'].filtered(
            lambda m: not self[f'module_{m.name}'] and m.state in ('installed', 'to upgrade'))

        if to_install or to_uninstall:
            self.env.flush_all()

        if to_uninstall:
            return {
                'type': 'ir.actions.act_window',
                'target': 'new',
                'name': _('Uninstall modules'),
                'view_mode': 'form',
                'res_model': 'base.module.uninstall',
                'context': {
                    'default_module_ids': to_uninstall.ids,
                },
            }

        installation_status = self._install_modules(to_install)

        if installation_status or to_uninstall:
            # After the uninstall/install calls, the registry and environments
            # are no longer valid. So we reset the environment.
            self.env.transaction.reset()

        # pylint: disable=next-method-called
        config = self.env['res.config'].next() or {}
        if config.get('type') not in ('ir.actions.act_window_close',):
            return config

        # force client-side reload (update user menu and current view)
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }