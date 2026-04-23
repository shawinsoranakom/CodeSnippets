def _get_alerts(self, moves, moves_data):
        # EXTENDS 'account'
        alerts = super()._get_alerts(moves, moves_data)

        peppol_formats = set(self.env['res.partner']._get_peppol_formats())
        if peppol_format_moves := moves.filtered(lambda m: moves_data[m]['invoice_edi_format'] in peppol_formats):
            not_configured_company_partners = peppol_format_moves.company_id.partner_id.filtered(
                lambda partner: not (partner.peppol_eas and partner.peppol_endpoint)
            )
            if not_configured_company_partners:
                alerts['account_edi_ubl_cii_configure_company'] = {
                    'message': _("Please fill in your company's VAT or Peppol Address to generate a complete XML file."),
                    'level': 'info',
                    'action_text': _("Configure"),
                    'action': not_configured_company_partners._get_records_action(),
                }
            not_configured_partners = peppol_format_moves.partner_id.commercial_partner_id.filtered(
                lambda partner: not (partner.peppol_eas and partner.peppol_endpoint)
            )
            if not_configured_partners:
                alerts['account_edi_ubl_cii_configure_partner'] = {
                    'message': _("Please fill in partner's VAT or Peppol Address."),
                    'level': 'info',
                    'action_text': _("View Partner(s)"),
                    'action': not_configured_partners._get_records_action(name=_("Check Partner(s)"))
                }

            if any(
                    self.env['account.edi.xml.ubl_bis3']._is_customer_behind_chorus_pro(partner)
                    for partner in peppol_format_moves.partner_id.commercial_partner_id
                ):
                chorus_pro = self.env['ir.module.module'].sudo().search([('name', '=', 'l10n_fr_facturx_chorus_pro')], limit=1)
                if chorus_pro and chorus_pro.state != 'installed':
                    alerts['account_edi_ubl_cii_chorus_pro_install'] = {
                        'message': _("Please install the french Chorus pro module to have all the specific rules."),
                        'level': 'info',
                        'action': chorus_pro._get_records_action(),
                        'action_text': _("Install Chorus Pro"),
                    }
        return alerts