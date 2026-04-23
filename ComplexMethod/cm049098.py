def _get_public_keys(self):
        """
        Fetches the list of KSeF certificates and returns a dictionary containing
        both the Symmetric and Token encryption public keys.
        """
        endpoint = f"{self.api_url}/security/public-key-certificates"
        headers = {'Accept': 'application/json'}
        try:
            response = requests.get(endpoint, headers=headers, timeout=TIMEOUT)
            response.raise_for_status()
            certs_data = response.json()

            public_keys = {
                'symmetric': None,
                'token': None,
            }

            for cert_info in certs_data:
                usage = cert_info.get('usage', [])

                if not set(usage) & {'SymmetricKeyEncryption', 'KsefTokenEncryption'}:
                    continue

                cert_b64 = cert_info['certificate']
                cert_der = base64.b64decode(cert_b64)
                cert = x509.load_der_x509_certificate(cert_der)
                public_key = cert.public_key()
                public_key_pem = public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ).decode('utf-8')

                if 'SymmetricKeyEncryption' in usage:
                    public_keys['symmetric'] = public_key_pem
                if 'KsefTokenEncryption' in usage:
                    public_keys['token'] = public_key_pem

            if not public_keys['symmetric'] or not public_keys['token']:
                raise UserError(self.env._("Could not find all required KSeF public keys ('SymmetricKeyEncryption' and 'KsefTokenEncryption')."))
            return public_keys

        except requests.exceptions.RequestException as e:
            raise UserError(self.env._("Could not fetch KSeF public keys: %s", e.response.text if e.response else e))