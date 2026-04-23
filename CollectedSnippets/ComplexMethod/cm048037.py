def _compute_l10n_in_warning(self):
        super()._compute_l10n_in_warning()
        gsp_provider = self.env["ir.config_parameter"].sudo().get_param("l10n_in.gsp_provider", "tera")
        if gsp_provider != "tera":
            return
        indian_invoice = self.filtered(lambda m: m.country_code == 'IN' and m.move_type != 'entry' and
            m.l10n_in_edi_status in ('to_send', 'sent') and not m.l10n_in_edi_error
        )
        edi_error_message = _(
            "⚠️ Important Notice – GSP Deprecation \n"
            "The currently selected GSP (Tera Soft) will be deprecated soon.\n"
            "To ensure uninterrupted e-Invoice and E-way operations, please switch to BVM GSP as per the"
        )
        if not self.env.is_admin():
            edi_error_message += _(
                "\n\nYou must contact your system administrator to update the GSP."
            )
        for move in indian_invoice:
            l10n_in_warning = move.l10n_in_warning or {}
            l10n_in_warning['in_edi_gsp_deprecation'] = {
                'message': edi_error_message,
                'action_text': _("Documentation"),
                'action': {
                    'name': _("Documentation"),
                    'type': 'ir.actions.act_url',
                    'url': 'https://www.odoo.com/documentation/19.0/applications/finance/fiscal_localizations/india.html#gsp-configuration',
                }
            }
            move.l10n_in_warning = l10n_in_warning