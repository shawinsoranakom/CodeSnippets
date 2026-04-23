def _build_vat_error_message(self, country_code, wrong_vat, record_label):
        # OVERRIDE account
        if self.env.context.get('company_id'):
            company = self.env['res.company'].browse(self.env.context['company_id'])
        else:
            company = self.env.company

        vat_label = _("VAT")
        if country_code and company.country_id and country_code == company.country_id.code and company.country_id.vat_label:
            vat_label = company.country_id.vat_label

        expected_format = _ref_vat.get(country_code.lower())
        expected_note = ""
        if expected_format:
            expected_note = ' \n' + _(
                'Note: the expected format is %(expected_format)s',
                 expected_format=expected_format
            )

        # Catch use case where the record label is about the public user (name: False)
        if 'False' not in record_label:
            return '\n' + _(
                'The %(vat_label)s number [%(wrong_vat)s] for %(record_label)s does not seem to be valid. %(expected_note)s',
                vat_label=vat_label,
                wrong_vat=wrong_vat,
                record_label=record_label,
                expected_note=expected_note
            )
        else:
            return '\n' + _(
                'The %(vat_label)s number [%(wrong_vat)s] does not seem to be valid. %(expected_note)s',
                vat_label=vat_label,
                wrong_vat=wrong_vat,
                expected_note=expected_note,
            )