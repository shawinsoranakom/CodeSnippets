def _generate_qr_code(self, silent_errors=False):
        """ Generates and returns a QR-code generation URL for this invoice,
        raising an error message if something is misconfigured.

        The chosen QR generation method is the one set in qr_method field if there is one,
        or the first eligible one found. If this search had to be performed and
        and eligible method was found, qr_method field is set to this method before
        returning the URL. If no eligible QR method could be found, we return None.
        """
        self.ensure_one()

        if not self.display_qr_code:
            return None

        qr_code_method = self.qr_code_method
        if qr_code_method:
            # If the user set a qr code generator manually, we check that we can use it
            error_msg = self.partner_bank_id._get_error_messages_for_qr(self.qr_code_method, self.partner_id, self.currency_id)
            if error_msg:
                raise UserError(error_msg)
        else:
            # Else we find one that's eligible and assign it to the invoice
            for candidate_method, _candidate_name in self.env['res.partner.bank'].get_available_qr_methods_in_sequence():
                error_msg = self.partner_bank_id._get_error_messages_for_qr(candidate_method, self.partner_id, self.currency_id)
                if not error_msg:
                    qr_code_method = candidate_method
                    break

        if not qr_code_method:
            # No eligible method could be found; we can't generate the QR-code
            return None

        unstruct_ref = self.payment_reference or self.name
        rslt = self.partner_bank_id.build_qr_code_base64(self.amount_residual, unstruct_ref, self.payment_reference, self.currency_id, self.partner_id, qr_code_method, silent_errors=silent_errors)

        # We only set qr_code_method after generating the url; otherwise, it
        # could be set even in case of a failure in the QR code generation
        # (which would change the field, but not refresh UI, making the displayed data inconsistent with db)
        self.qr_code_method = qr_code_method

        return rslt