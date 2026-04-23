def qfpay_sign_request(self, payload):
        self.ensure_one()
        if not self.env.su and not self.env.user.has_group('point_of_sale.group_pos_user'):
            raise AccessDenied()

        if self.use_payment_terminal != 'qfpay':
            raise UserError(_('This method can only be used with QFPay payment terminal.'))

        key = self.sudo().qfpay_pos_key
        # AES IV is a constant as stated in the documentation
        aes_iv = 'qfpay202306_hjsh'

        # Sort the payload items and format
        payload_items = sorted((k, '' if v is None else v) for k, v in payload.items())
        formated_payload = ','.join(f"{k}='{v}'" if isinstance(v, str) else f"{k}={v}" for k, v in payload_items)
        formated_payload = '{' + formated_payload + '}'

        # Generate Digest
        md5 = hashlib.md5()
        md5.update((formated_payload + key).encode('utf-8'))
        digest = md5.hexdigest().upper()

        # Prepare the payload to encrypt
        payload_to_encrypt = "{content:" + formated_payload + ", digest:'" + digest + "'}"

        # Encrypt the payload
        cipher = Cipher(algorithms.AES(key.encode('utf-8')), modes.CBC(aes_iv.encode('utf-8')))
        encryptor = cipher.encryptor()
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(payload_to_encrypt.encode('utf-8')) + padder.finalize()
        encrypted = encryptor.update(padded_data) + encryptor.finalize()
        return base64.b64encode(encrypted).decode('utf-8')