def _l10n_ch_get_qr_vals(self, amount, currency, debtor_partner, free_communication, structured_communication):
        filter_text = self._l10n_ch_filter_text
        comment = ""
        if free_communication:
            free_communication = filter_text(free_communication)
            comment = (free_communication[:137] + '...') if len(free_communication) > 140 else free_communication

        cred_street, cred_street_number, cred_zip, cred_city = self._get_partner_address_lines(self.partner_id)
        debt_street, debt_street_number, debt_zip, debt_city = self._get_partner_address_lines(debtor_partner)

        # Compute reference type (empty by default, only mandatory for QR-IBAN,
        # and must then be 27 characters-long, with mod10r check digit as the 27th one)
        reference_type = 'NON'
        reference = ''
        acc_number = self.sanitized_acc_number

        if self.l10n_ch_qr_iban:
            # _check_for_qr_code_errors ensures we can't have a QR-IBAN without a QR-reference here
            reference_type = 'QRR'
            reference = structured_communication
            acc_number = sanitize_account_number(self.l10n_ch_qr_iban)
        elif self._is_iso11649_reference(structured_communication):
            reference_type = 'SCOR'
            reference = structured_communication.replace(' ', '')

        currency = currency or self.currency_id or self.company_id.currency_id
        cred_name = filter_text(self.acc_holder_name or self.partner_id.name)
        debt_name = filter_text(debtor_partner.commercial_partner_id.name)

        result = [
            'SPC',                                                # QR Type
            '0200',                                               # Version
            '1',                                                  # Coding Type
            acc_number,                                           # IBAN / QR-IBAN
            'S',                                                  # Creditor Address Type
            cred_name[:70],                                       # Creditor Name
            cred_street,                                          # Creditor Street Name
            cred_street_number,                                   # Creditor Building Number
            cred_zip,                                             # Creditor Postal Code
            cred_city,                                            # Creditor Town
            self.partner_id.country_id.code,                      # Creditor Country
            '',                                                   # Ultimate Creditor Address Type
            '',                                                   # Name
            '',                                                   # Ultimate Creditor Address Line 1
            '',                                                   # Ultimate Creditor Address Line 2
            '',                                                   # Ultimate Creditor Postal Code
            '',                                                   # Ultimate Creditor Town
            '',                                                   # Ultimate Creditor Country
            '{:.2f}'.format(amount),                              # Amount
            currency.name,                                        # Currency
            'S',                                                  # Ultimate Debtor Address Type
            debt_name[:70],                                       # Ultimate Debtor Name
            debt_street,                                          # Ultimate Debtor Street Name
            debt_street_number,                                   # Ultimate Debtor Building Number
            debt_zip,                                             # Ultimate Debtor Postal Code
            debt_city,                                            # Ultimate Debtor Town
            debtor_partner.country_id.code,                       # Ultimate Debtor Country
            reference_type,                                       # Reference Type
            reference,                                            # Reference
            comment,                                              # Unstructured Message
            'EPD',                                                # Mandatory trailer part
        ]

        # newlines shift field content to a different line, causing the QR code to be rejected
        return [line.replace('\n', ' ') for line in result]