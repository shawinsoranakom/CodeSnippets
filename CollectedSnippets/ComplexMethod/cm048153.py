def _compute_private_key(self):
        attachments = self.env['ir.attachment'].search([
            ('res_model', '=', 'certificate.key'),
            ('res_field', '=', 'content'),
            ('res_id', 'in', self.ids)
        ])
        content_to_key_id = {(att.datas, att.company_id.id): att.res_id for att in attachments}

        for certificate in self:
            if not certificate.pem_certificate:
                certificate.private_key_id = None
                continue

            if certificate.private_key_id:
                continue

            # Create the private key in case of PKCS12 File and no private key is set
            if certificate.content_format == 'pkcs12':
                content = certificate.with_context(bin_size=False).content
                pkcs12_password = certificate.pkcs12_password.encode('utf-8') if certificate.pkcs12_password else None
                key, _cert, _additional_certs = pkcs12.load_key_and_certificates(base64.b64decode(content), pkcs12_password)

                if key:
                    pem_key = base64.b64encode(key.private_bytes(
                        encoding=Encoding.PEM,
                        format=serialization.PrivateFormat.PKCS8,
                        encryption_algorithm=serialization.NoEncryption()
                    ))
                    key_id = content_to_key_id.get((pem_key, certificate.company_id.id))
                    if not key_id:
                        key_id = self.env['certificate.key'].create({
                            'name': (certificate.subject_common_name or certificate.name or "") + ".key",
                            'content': pem_key,
                            'company_id': certificate.company_id.id,
                        })
                    certificate.private_key_id = key_id