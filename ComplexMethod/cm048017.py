def _compute_sending_method_checkboxes(self):
        """ EXTENDS 'account'
        If Customer is not valid on Peppol, we disable the checkbox. Also add the proxy mode if not in prod.
        """
        super()._compute_sending_method_checkboxes()
        for wizard in self:
            if peppol_checkbox := wizard.sending_method_checkboxes.get('peppol'):
                peppol_partner = wizard.move_id.partner_id.commercial_partner_id.with_company(wizard.company_id)
                peppol_proxy_mode = wizard.company_id._get_peppol_edi_mode()
                if peppol_partner.peppol_verification_state == 'not_valid':
                    addendum_disable_reason = _(' (Customer not on Peppol)')
                elif peppol_partner.peppol_verification_state == 'not_verified':
                    addendum_disable_reason = _(' (no VAT)')
                elif wizard.company_id._have_unauthorized_peppol_parent_company():
                    addendum_disable_reason = _(' (no access)')
                else:
                    addendum_disable_reason = ''
                vals_not_valid = {'readonly': True, 'checked': False} if addendum_disable_reason else {}
                addendum_mode = ''
                if peppol_proxy_mode == 'test':
                    addendum_mode = _(' (Test)')
                elif peppol_proxy_mode == 'demo':
                    addendum_mode = _(' (Demo)')
                if addendum_disable_reason or addendum_mode:
                    wizard.sending_method_checkboxes = {
                        **wizard.sending_method_checkboxes,
                        'peppol': {
                            **peppol_checkbox,
                            **vals_not_valid,
                            'label': _(
                                '%(peppol_label)s%(disable_reason)s%(peppol_proxy_mode)s',
                                peppol_label=peppol_checkbox['label'],
                                disable_reason=addendum_disable_reason,
                                peppol_proxy_mode=addendum_mode,
                            ),
                        }
                    }