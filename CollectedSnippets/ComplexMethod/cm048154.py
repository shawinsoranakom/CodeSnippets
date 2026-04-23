def _compute_pem_certificate(self):
        for certificate in self:
            content = certificate.with_context(bin_size=False).content

            if not content:
                certificate.pem_certificate = None
                certificate.subject_common_name = None
                certificate.content_format = None
                certificate.date_start = None
                certificate.date_end = None
                certificate.serial_number = None
                certificate.loading_error = ""

            else:
                content = base64.b64decode(content)
                cert = None

                # Try to load the certificate in different format starting with DER then PKCS12 and
                # finally PEM. If none succeeded, we report an error.
                try:
                    cert = x509.load_der_x509_certificate(content)
                    certificate.content_format = 'der'
                except ValueError:
                    pass
                if not cert:
                    try:
                        pkcs12_password = certificate.pkcs12_password.encode('utf-8') if certificate.pkcs12_password else None
                        _key, cert, _additional_certs = pkcs12.load_key_and_certificates(content, pkcs12_password)
                        certificate.content_format = 'pkcs12'
                    except ValueError:
                        pass
                if not cert:
                    try:
                        cert = x509.load_pem_x509_certificate(content)
                        certificate.content_format = 'pem'
                    except ValueError:
                        pass

                if not cert:
                    certificate.pem_certificate = None
                    certificate.subject_common_name = None
                    certificate.content_format = None
                    certificate.date_start = None
                    certificate.date_end = None
                    certificate.serial_number = None

                    if not certificate.pkcs12_password:
                        certificate.loading_error = ""
                    else:
                        certificate.loading_error = _(
                            "This certificate could not be loaded. Either the content or the password is erroneous.")
                    continue

                try:
                    common_name = cert.subject.get_attributes_for_oid(x509.NameOID.COMMON_NAME)
                    certificate.subject_common_name = common_name[0].value if common_name else ""
                except ValueError:
                    certificate.subject_common_name = None

                certificate.loading_error = ""

                # Extract certificate data
                certificate.pem_certificate = base64.b64encode(cert.public_bytes(Encoding.PEM))
                certificate.serial_number = cert.serial_number
                if parse_version(metadata.version('cryptography')) < parse_version('42.0.0'):
                    certificate.date_start = cert.not_valid_before
                    certificate.date_end = cert.not_valid_after
                else:
                    certificate.date_start = cert.not_valid_before_utc.replace(tzinfo=None)
                    certificate.date_end = cert.not_valid_after_utc.replace(tzinfo=None)