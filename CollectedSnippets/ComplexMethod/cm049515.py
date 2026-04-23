def _compute_sending_method_checkboxes(self):
        """ EXTENDS 'account'
        If Customer is not valid on Nemhandel, we disable the checkbox. Also add the proxy mode if not in prod.
        """
        super()._compute_sending_method_checkboxes()
        for wizard in self:
            nemhandel_checkbox = wizard.sending_method_checkboxes.get('nemhandel')
            if not nemhandel_checkbox:
                continue

            nemhandel_partner = wizard.move_id.partner_id.commercial_partner_id.with_company(wizard.company_id)
            nemhandel_proxy_mode = wizard.company_id._get_nemhandel_edi_mode()
            if nemhandel_partner.nemhandel_verification_state == 'not_valid':
                addendum_disable_reason = _(' (Customer not on Nemhandel)')
            elif nemhandel_partner.nemhandel_verification_state == 'not_verified':
                addendum_disable_reason = _(' (no VAT)')
            else:
                addendum_disable_reason = ''
            vals_not_valid = {'readonly': True, 'checked': False} if addendum_disable_reason else {}
            addendum_mode = ''
            if nemhandel_proxy_mode == 'test':
                addendum_mode = _(' (Test)')
            elif nemhandel_proxy_mode == 'demo':
                addendum_mode = _(' (Demo)')
            if addendum_disable_reason or addendum_mode:
                wizard.sending_method_checkboxes = {
                    **wizard.sending_method_checkboxes,
                    'nemhandel': {
                        **nemhandel_checkbox,
                        **vals_not_valid,
                        'label': f"{nemhandel_checkbox['label']}{addendum_disable_reason}{addendum_mode}",
                    },
                }