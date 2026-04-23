def write(self, vals):
        self._check_header_footer(vals)
        self._reset_default_on_vals(vals)
        if ('is_order_printer' in vals and not vals['is_order_printer']):
            vals['printer_ids'] = [fields.Command.clear()]

        bypass_payment_method_ids_forbidden_change = self.env.context.get('bypass_payment_method_ids_forbidden_change', False)

        self._preprocess_x2many_vals_from_settings_view(vals)
        vals = self._keep_new_vals(vals)
        opened_session = self.mapped('session_ids').filtered(lambda s: s.state != 'closed')
        if opened_session:
            forbidden_fields = []
            for key in self._get_forbidden_change_fields():
                if key in vals.keys():
                    if bypass_payment_method_ids_forbidden_change and key == 'payment_method_ids':
                        continue
                    # Allow activating a pos config even if it has an open session, but don't allow deactivating it.
                    if key == 'active' and vals['active']:
                        continue
                    field_name = self._fields[key].get_description(self.env)["string"]
                    forbidden_fields.append(field_name)

            if len(forbidden_fields) > 0:
                raise UserError(_(
                    "Unable to modify this PoS Configuration because you can't modify %s while a session is open.",
                    ", ".join(forbidden_fields)
                ))

        result = super(PosConfig, self).write(vals)

        for config in self:
            if config.use_presets and config.default_preset_id and config.default_preset_id.id not in config.available_preset_ids.ids:
                config.available_preset_ids |= config.default_preset_id

        self.sudo()._set_fiscal_position()
        self.sudo()._check_modules_to_install()
        self.sudo()._check_groups_implied()
        if 'is_order_printer' in vals:
            self._update_preparation_printers_menuitem_visibility()
        return result