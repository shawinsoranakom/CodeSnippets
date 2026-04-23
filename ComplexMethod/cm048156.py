def _compute_pem_key(self):
        for key in self:
            content = key.with_context(bin_size=False).content
            if not content:
                key.pem_key = None
                key.public = None
                key.loading_error = ""
            else:
                pkey_content = base64.b64decode(content)
                pkey_password = key.password.encode('utf-8') if key.password else None

                # Try to load the key in different format starting with DER then PEM for private then public keys.
                # If none succeeded, we report an error.
                pkey = None
                try:
                    pkey = serialization.load_der_private_key(pkey_content, pkey_password)
                    key.public = False
                except (ValueError, TypeError):
                    pass

                if not pkey:
                    try:
                        pkey = serialization.load_pem_private_key(pkey_content, pkey_password)
                        key.public = False
                    except (ValueError, TypeError):
                        pass

                if not pkey:
                    try:
                        pkey = serialization.load_der_public_key(pkey_content)
                        key.public = True
                    except (ValueError, TypeError):
                        pass

                if not pkey:
                    try:
                        pkey = serialization.load_pem_public_key(pkey_content)
                        key.public = True
                    except (ValueError, TypeError):
                        pass

                if not pkey:
                    key.pem_key = None
                    key.public = None
                    key.loading_error = _("This key could not be loaded. Either its content or its password is erroneous.")
                    continue

                if key.public:
                    key.pem_key = base64.b64encode(pkey.public_bytes(
                        encoding=Encoding.PEM,
                        format=serialization.PublicFormat.SubjectPublicKeyInfo,
                    ))
                else:
                    encryption = serialization.BestAvailableEncryption(pkey_password) if pkey_password else serialization.NoEncryption()
                    key.pem_key = base64.b64encode(pkey.private_bytes(
                        encoding=Encoding.PEM,
                        format=serialization.PrivateFormat.PKCS8,
                        encryption_algorithm=encryption,
                    ))

                key.loading_error = ""