def _set_l10n_it_edi_register(self):
        for config in self:
            company = config.company_id._l10n_it_get_edi_company()
            company.l10n_it_edi_register = config.l10n_it_edi_register
            proxy_user = self.env['account_edi_proxy_client.user'].sudo().search([
                ('company_id', '=', company.id),
                ('proxy_type', '=', 'l10n_it_edi'),
                ('edi_mode', '!=', 'demo'),  # make sure it's a "real" proxy_user (edi_mode is 'test' or 'prod')
            ], limit=1)

            if proxy_user and proxy_user.active != config.l10n_it_edi_register:
                # Deactivate / Reactive the current proxy user based on the config's l10n_it_edi_register value
                proxy_user._toggle_proxy_user_active()
            elif config.l10n_it_edi_register and not proxy_user:
                # Create a new proxy user
                edi_mode = self.env['ir.config_parameter'].sudo().get_param('l10n_it_edi.proxy_user_edi_mode') or 'prod'
                proxy_user = self._create_proxy_user(company, edi_mode)

            if proxy_user:
                # Delete any previously created demo proxy user
                self.env['account_edi_proxy_client.user'].sudo().search([
                    ('company_id', '=', company.id),
                    ('proxy_type', '=', 'l10n_it_edi'),
                    ('edi_mode', '=', 'demo'),
                    ('id', '!=', proxy_user.id),
                ]).unlink()