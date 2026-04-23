def _constrains_certificate_key_compatibility(self):
        for certificate in self:
            pem_certificate = certificate.with_context(bin_size=False).pem_certificate
            if pem_certificate:
                cert = x509.load_pem_x509_certificate(base64.b64decode(pem_certificate))
                cert_public_key_bytes = cert.public_key().public_bytes(
                    encoding=Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                )

                if certificate.private_key_id:
                    if certificate.private_key_id.loading_error:
                        raise ValidationError(certificate.private_key_id.loading_error)
                    pkey_public_key_bytes = base64.b64decode(
                        certificate.private_key_id._get_public_key_bytes(encoding='pem')
                    )
                    if not constant_time.bytes_eq(pkey_public_key_bytes, cert_public_key_bytes):
                        raise ValidationError(_("The certificate and private key are not compatible."))

                if certificate.public_key_id:
                    if certificate.public_key_id.loading_error:
                        raise ValidationError(certificate.public_key_id.loading_error)
                    pkey_public_key_bytes = base64.b64decode(
                        certificate.public_key_id._get_public_key_bytes(encoding='pem')
                    )
                    if not constant_time.bytes_eq(pkey_public_key_bytes, cert_public_key_bytes):
                        raise ValidationError(_("The certificate and public key are not compatible."))