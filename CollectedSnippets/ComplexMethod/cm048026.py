def button_account_peppol_check_partner_endpoint(self, company=None):
        """ A basic check for whether a participant is reachable at the given
        Peppol participant ID - peppol_eas:peppol_endpoint (ex: '9999:test')
        The SML (Service Metadata Locator) assigns a DNS name to each peppol participant.
        This DNS name resolves into the SMP (Service Metadata Publisher) of the participant.
        The DNS address is of the following form:
        strip-trailing(base32(sha256(lowercase(ID-VALUE))),"=") + "." + ID-SCHEME + "." + SML-ZONE-NAME
        The lookup should be done on NAPTR DNS from 2025-11-01
        (ref:https://peppol.helger.com/public/locale-en_US/menuitem-docs-doc-exchange)
        """
        self.ensure_one()
        if not company:
            company = self.env.company

        self_partner = self.with_company(company)
        if not self_partner.peppol_eas or not self_partner.peppol_endpoint:
            return False
        old_value = self_partner.peppol_verification_state
        new_value = self._get_peppol_verification_state(
            self_partner.peppol_endpoint,
            self_partner.peppol_eas,
            self_partner._get_peppol_edi_format(),
        )

        if (
                new_value != 'valid'
                and self_partner.peppol_eas in ('0208', '9925')
        ):
            # checks the inverse `eas:endpoint` if the belgian user was not found on Peppol in the first try
            inverse_eas = '9925' if self_partner.peppol_eas == '0208' else '0208'
            inverse_endpoint = f'BE{self_partner.peppol_endpoint}' if self_partner.peppol_eas == '0208' else self_partner.peppol_endpoint[2:]
            if (peppol_state := self._get_peppol_verification_state(inverse_endpoint, inverse_eas, self_partner._get_peppol_edi_format())) == 'valid':
                self_partner.write({
                    'peppol_eas': inverse_eas,
                    'peppol_endpoint': inverse_endpoint,
                })
                new_value = peppol_state

        if old_value != new_value:
            self_partner.peppol_verification_state = new_value
            self._log_verification_state_update(company, old_value, self_partner.peppol_verification_state)
        return False