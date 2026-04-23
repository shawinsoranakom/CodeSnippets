def _build_qr_code_vals(self, amount, free_communication, structured_communication, currency, debtor_partner, qr_method=None, silent_errors=True):
        """ Returns the QR-code vals needed to generate the QR-code report link to pay this account with the given parameters,
        or None if no QR-code could be generated.

        :param amount: The amount to be paid
        :param free_communication: Free communication to add to the payment when generating one with the QR-code
        :param structured_communication: Structured communication to add to the payment when generating one with the QR-code
        :param currency: The currency in which amount is expressed
        :param debtor_partner: The partner to which this QR-code is aimed (so the one who will have to pay)
        :param qr_method: The QR generation method to be used to make the QR-code. If None, the first one giving a result will be used.
        :param silent_errors: If true, forbids errors to be raised if some tested QR-code format can't be generated because of incorrect data.
        """
        if not self:
            return None

        self.ensure_one()
        if not currency:
            raise UserError(_("Currency must always be provided in order to generate a QR-code"))

        available_qr_methods = self.get_available_qr_methods_in_sequence()
        candidate_methods = qr_method and [(qr_method, dict(available_qr_methods)[qr_method])] or available_qr_methods
        for candidate_method, candidate_name in candidate_methods:
            error_message = self._get_error_messages_for_qr(candidate_method, debtor_partner, currency)
            if not error_message:
                error_message = self._check_for_qr_code_errors(candidate_method, amount, currency, debtor_partner, free_communication, structured_communication)

                if not error_message:
                    return {
                        'qr_method': candidate_method,
                        'amount': amount,
                        'currency': currency,
                        'debtor_partner': debtor_partner,
                        'free_communication': free_communication,
                        'structured_communication': structured_communication,
                    }

            if not silent_errors:
                raise UserError(self.env._("The following error prevented '%(candidate)s' QR-code to be generated though it was detected as eligible: ", candidate=candidate_name) + error_message)

        return None