def action_validate_tin(self):
        """ Calling this action will reach our EDI proxy in order to validate the TIN against the provided identification information. """
        self.ensure_one()
        if not self._l10n_my_edi_get_tin_for_myinvois() or not self.l10n_my_identification_type or not self.l10n_my_identification_number:
            raise UserError(self.env._('In order to validate the TIN, you must provide the Identification type and number.'))

        # Sudo to allow a user without access to the proxy user to validate the ID if needed.
        proxy_user = self.env.company.sudo().l10n_my_edi_proxy_user_id
        if not proxy_user:
            raise UserError(self.env._("Please register for the E-Invoicing service in the settings first."))

        response = proxy_user._l10n_my_edi_contact_proxy('api/l10n_my_edi/1/validate_tin', params={
            'identification_values': {
                'tin': self._l10n_my_edi_get_tin_for_myinvois(),
                'id_type': self.l10n_my_identification_type,
                'id_val': self.l10n_my_identification_number,
            },
        })

        if 'error' in response:
            ref = response['error']['reference']
            # No need to rollback, we don't want to be blocking on that.
            if ref == 'document_tin_not_found':
                self._message_log(body=self.env._('MyInvois was not able to match the TIN with the provided identification number.\nThis may happen when using generic TIN and will not prevent you from invoicing.'))
                self.l10n_my_tin_validation_state = 'invalid'
            else:
                self._message_log(body=self.env._('An unexpected error occurred while validating the TIN. Please try again later.'))
        else:
            self.l10n_my_tin_validation_state = 'valid' if response.get('success') else 'invalid'