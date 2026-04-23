def _check_for_qr_code_errors(self, qr_method, amount, currency, debtor_partner, free_communication, structured_communication):
        def _partner_fields_set(partner):
            return partner.zip and \
                   partner.city and \
                   partner.country_id.code and \
                   (partner.street or partner.street2)

        if qr_method == 'ch_qr':
            if not _partner_fields_set(self.partner_id):
                return _("The partner set on the bank account meant to receive the payment (%s) must have a complete postal address (street, zip, city and country).", self.acc_number)

            if debtor_partner and not _partner_fields_set(debtor_partner):
                return _("The partner must have a complete postal address (street, zip, city and country).")

            if self.l10n_ch_qr_iban and not self._is_qr_reference(structured_communication):
                return _("When using a QR-IBAN as the destination account of a QR-code, the payment reference must be a QR-reference.")

            debtor_check = self._l10n_ch_qr_debtor_check(debtor_partner)
            if debtor_check:
                return debtor_check

        return super()._check_for_qr_code_errors(qr_method, amount, currency, debtor_partner, free_communication, structured_communication)