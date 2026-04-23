def write(self, vals):
        # Keep track if view was modified. That will be useful for the --dev mode
        # to prefer modified arch over file arch.
        if 'arch_updated' not in vals and ('arch' in vals or 'arch_base' in vals) and 'install_filename' not in self.env.context:
            vals['arch_updated'] = True

        # drop the corresponding view customizations (used for dashboards for example), otherwise
        # not all users would see the updated views
        custom_view = self.env['ir.ui.view.custom'].sudo().search([('ref_id', 'in', self.ids)])
        if custom_view:
            custom_view.unlink()

        self.env.registry.clear_cache('templates')
        if 'arch_db' in vals and not self.env.context.get('no_save_prev'):
            vals['arch_prev'] = self.arch_db

        res = super().write(self._compute_defaults(vals))

        # Check the xml of the view if it gets re-activated or changed.
        if 'active' in vals or 'arch_db' in vals or 'inherit_id' in vals:
            self._check_xml()

        return res