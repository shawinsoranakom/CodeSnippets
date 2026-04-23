def _prepare_post_params_bi(self, is_sale):
        """Web service parameters for Bizkaia."""
        company = self.company_id
        freelancer = company._l10n_es_freelancer()

        if is_sale:
            xml_to_send = self._generate_final_xml_bi(freelancer=freelancer)
            lroe_str = etree.tostring(xml_to_send)
        else:
            lroe_str = self.xml_attachment_id.raw

        lroe_bytes = gzip.compress(lroe_str)


        return {
            'url': get_key(company.l10n_es_tbai_tax_agency, 'cancel_url_' if self.is_cancel else 'post_url_', company.l10n_es_tbai_test_env),
            'headers': {
                'Accept-Encoding': 'gzip',
                'Content-Encoding': 'gzip',
                'Content-Length': str(len(lroe_str)),
                'Content-Type': 'application/octet-stream',
                'eus-bizkaia-n3-version': '1.0',
                'eus-bizkaia-n3-content-type': 'application/xml',
                'eus-bizkaia-n3-data': json.dumps({
                    'con': 'LROE',
                    'apa': '2.1' if freelancer and not is_sale else '1.1' if is_sale else '2',
                    'inte': {
                        'nif': company.vat[2:] if company.vat.startswith('ES') else company.vat,
                        'nrs': company.name,
                    },
                    'drs': {
                        'mode': '140' if freelancer else '240',
                        'ejer': str(self.date.year),
                    }
                }),
            },
            'pkcs12_data': company.l10n_es_tbai_certificate_id,
            'data': lroe_bytes,
        }