def _l10n_pl_edi_ksef_authenticate(self):
        """
            Orchestrates the entire authentication flow using the service.
        """
        self.ensure_one()

        vat = self.company_id.vat
        if not vat or not vat.startswith('PL'):
            raise ValidationError(self.env._("A polish VAT number must be set on your company."))
        if not self.l10n_pl_edi_certificate:
            raise ValidationError(self.env._("Please set up a valid KSeF Certificate, with its Private Key set"))

        nip = stdnum.pl.nip.compact(vat)

        ksef_service = KsefApiService(self.company_id)
        temp_token, ref_number = None, None

        if not self.l10n_pl_edi_certificate.private_key_id:
            raise ValidationError(self.env._(
                "The selected certificate record (%(name)s) is missing a private key.",
                name=self.l10n_pl_edi_certificate.display_name
            ))

        key_bytes = base64.b64decode(self.l10n_pl_edi_certificate.private_key_id.pem_key)
        cert_bytes = base64.b64decode(self.l10n_pl_edi_certificate.pem_certificate)
        private_key_password = (self.l10n_pl_edi_certificate.private_key_id.password or "").encode("utf-8") or None
        if key_bytes and cert_bytes:
            signer = XadesSigner(key_bytes, cert_bytes, private_key_password)
        else:
            raise UserError(self.env._("KSeF certificate and private key are not set."))

        challenge_data = ksef_service.get_challenge()
        challenge_code = challenge_data.get('challenge')

        signed_xml = signer.sign_authentication_challenge(challenge_code, nip)
        token_data = ksef_service.authenticate_xades(signed_xml)

        temp_token = token_data.get('authenticationToken', {}).get('token')
        ref_number = token_data.get('referenceNumber')
        if not temp_token or not ref_number:
            raise ValidationError(self.env._("Failed to initiate KSeF authentication."))

        status_data = ksef_service.check_auth_status(ref_number, temp_token)
        if status_data.get('status', {}).get('code') != 200:
            raise ValidationError(self.env._("Authentication with KSeF failed."))

        token_data = ksef_service.redeem_token(temp_token)
        access_token = token_data.get('accessToken', {}).get('token')
        refresh_token = token_data.get('refreshToken', {}).get('token')
        if not access_token or not refresh_token:
            raise ValidationError(self.env._("Failed to retrieve access or refresh tokens."))

        self.company_id.sudo().write({
            'l10n_pl_edi_access_token': access_token,
            'l10n_pl_edi_refresh_token': refresh_token,
        })