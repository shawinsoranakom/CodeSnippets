def _verify_with_key(self, signed_message, signature, pem_key, signature_algorithm='sha256'):
        """  Return the verification of the signature """

        def check_valid_signature_algorithm():
            if signature_algorithm not in STR_TO_HASH:
                raise UserError(f"Unsupported signature algorithm '{signature_algorithm}'. Currently supported: sha1 and sha256.")  # pylint: disable=missing-gettext

        if not isinstance(signed_message, bytes):
            signed_message = signed_message.encode('utf-8')

        if not isinstance(pem_key, bytes):
            pem_key = pem_key.encode('utf-8')

        try:
            public_key = serialization.load_pem_public_key(base64.b64decode(pem_key))
        except ValueError:
            raise UserError(_("The public key could not be loaded."))

        match public_key:
            case ec.EllipticCurvePublicKey():
                check_valid_signature_algorithm(signature_algorithm)
                try:
                    public_key.verify(
                        signature,
                        signed_message,
                        ec.ECDSA(STR_TO_HASH[signature_algorithm])
                    )
                    return True
                except InvalidSignature:
                    return False
            case rsa.RSAPublicKey():
                check_valid_signature_algorithm(signature_algorithm)
                try:
                    public_key.verify(
                        signature,
                        signed_message,
                        padding.PKCS1v15(),
                        STR_TO_HASH[signature_algorithm],
                    )
                    return True
                except InvalidSignature:
                    return False
            case ed25519.Ed25519PublicKey():
                try:
                    public_key.verify(
                        signature,
                        signed_message,
                    )
                    return True
                except InvalidSignature:
                    return False
            case _:
                raise UserError(_(
                    "Unsupported asymmetric cryptography algorithm '%s'. Currently supported for signature: EC and RSA.",
                    repr(public_key),
                ))