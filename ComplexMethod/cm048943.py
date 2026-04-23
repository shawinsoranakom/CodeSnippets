def _get_error_messages_for_qr(self, qr_method, debtor_partner, currency):
        if qr_method == 'sct_qr':
            # Some countries share the same IBAN country code
            # (e.g. Åland Islands and Finland IBANs are 'FI', but Åland Islands' code is 'AX').
            sepa_country_codes = self.env.ref('base.sepa_zone').country_ids.mapped('code')
            non_iban_codes = {'AX', 'NC', 'YT', 'TF', 'BL', 'RE', 'MF', 'GP', 'PM', 'PF', 'GF', 'MQ', 'JE', 'GG', 'IM'}
            sepa_iban_codes = {code for code in sepa_country_codes if code not in non_iban_codes}
            error_messages = []
            if currency.name != 'EUR':
                error_messages.append(_("Can't generate a SEPA QR Code with the %s currency.", currency.name))
            if self.acc_type != 'iban':
                error_messages.append(_("Can't generate a SEPA QR code if the account type isn't IBAN."))
            if not (self.sanitized_acc_number and self.sanitized_acc_number[:2] in sepa_iban_codes):
                error_messages.append(_("Can't generate a SEPA QR code with a non SEPA iban."))
            if len(error_messages) > 0:
                return '\r\n'.join(error_messages)
            return None
        return super()._get_error_messages_for_qr(qr_method, debtor_partner, currency)