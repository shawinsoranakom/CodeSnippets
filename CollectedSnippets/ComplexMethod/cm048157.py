def _sign_with_key(self, message, pem_key, pwd=None, hashing_algorithm='sha256', formatting='encodebytes'):
        ''' Compute and return the message's signature for a given private key.

        :param str|bytes message: The message to sign
        :param str|bytes pem_key: A base64 encoded private key in the PEM format
        :param str|bytes pwd: A password to decrypt the PEM key
        :param optional,default='sha1' hashing_algorithm: The digest algorithm to use. Currently, only 'sha1' and 'sha256' are available.
        :param optional,default='encodebytes' formatting: The formatting of the returned bytes
            - 'encodebytes' returns a base64-encoded block of 76 characters lines
            - 'base64' returns the raw base64-encoded data
            - other returns non-encoded data
        :return: The formatted signature bytes of the message
        :rtype: bytes
        '''

        if not isinstance(message, bytes):
            message = message.encode('utf-8')
        if not isinstance(pem_key, bytes):
            pem_key = pem_key.encode('utf-8')
        if pwd and not isinstance(pwd, bytes):
            pwd = pwd.encode('utf-8')

        if hashing_algorithm not in STR_TO_HASH:
            raise UserError(f"Unsupported hashing algorithm '{hashing_algorithm}'. Currently supported: sha1 and sha256.")  # pylint: disable=missing-gettext

        try:
            private_key = serialization.load_pem_private_key(base64.b64decode(pem_key), pwd or None)
        except ValueError:
            raise UserError(_("The private key could not be loaded."))

        match private_key:
            case ec.EllipticCurvePrivateKey():
                signature = private_key.sign(
                    message,
                    ec.ECDSA(STR_TO_HASH[hashing_algorithm])
                )
            case rsa.RSAPrivateKey():
                signature = private_key.sign(
                    message,
                    padding.PKCS1v15(),
                    STR_TO_HASH[hashing_algorithm]
                )
            case ed25519.Ed25519PrivateKey():
                signature = private_key.sign(message)
            case _:
                raise UserError(_(
                    "Unsupported asymmetric cryptography algorithm '%s'. Currently supported for signature: ED25519, EC and RSA.",
                    type(private_key)))

        return _get_formatted_value(signature, formatting=formatting)