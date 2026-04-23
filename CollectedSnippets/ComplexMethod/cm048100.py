def _l10n_gr_edi_add_address_vals(self, values):
        """
        Adds all the address values needed for the ``invoice_vals`` dictionary.
        The only guaranteed keys in to add in the dictionary is the issuer's VAT, country code, and branch number.
        Everything else is only displayed on some specific case/configuration.
        The appended dictionary will have the following additional keys:
        {
            'issuer_vat_number': <str>,
            'issuer_country': <str>,
            'issuer_branch': <int>,
            'issuer_name': <str | None>,
            'issuer_postal_code': <str | None>,
            'issuer_city': <str | None>,
            'counterpart_vat': <str | None>,
            'counterpart_country': <str | None>,
            'counterpart_branch': <int | None>,
            'counterpart_name': <str | None>,
            'counterpart_postal_code': <str | None>,
            'counterpart_city': <str | None>,
            'counterpart_postal_code': <str | None>,
            'counterpart_city': <str | None>,
        }
        :param dict values: dictionary where the address values will be added
        :rtype: dict[str, str|int]
        """
        self.ensure_one()
        issuer_not_from_greece = self.company_id.country_code != 'GR'
        inv_type_allows_counterpart = self.l10n_gr_edi_inv_type not in TYPES_WITH_FORBIDDEN_COUNTERPART
        partner_not_from_greece = self.partner_id.country_code != 'GR'
        inv_type_require_counterpart = self.l10n_gr_edi_inv_type in TYPES_WITH_MANDATORY_COUNTERPART

        conditional_address_keys = ('issuer_name', 'issuer_postal_code', 'issuer_city', 'counterpart_vat', 'counterpart_country',
                                    'counterpart_branch', 'counterpart_name', 'counterpart_postal_code', 'counterpart_city')
        values.update({
            'issuer_vat_number': self.company_id.vat.replace('EL', '').replace('GR', ''),
            'issuer_country': self.company_id.country_code,
            'issuer_branch': self.company_id.l10n_gr_edi_branch_number or 0,
            **dict.fromkeys(conditional_address_keys),
        })

        if issuer_not_from_greece:
            values.update({
                'issuer_name': self.company_id.name.encode('ISO-8859-7'),
                'issuer_postal_code': self.company_id.zip,
                'issuer_city': (self.company_id.city or "").encode('ISO-8859-7') or None,
            })

        if inv_type_allows_counterpart:
            values.update({
                'counterpart_vat': self.commercial_partner_id.vat.replace('EL', '').replace('GR', ''),
                'counterpart_country': self.commercial_partner_id.country_code,
                'counterpart_branch': (self.commercial_partner_id.l10n_gr_edi_branch_number or 0),
            })
            if partner_not_from_greece:
                values['counterpart_name'] = self.commercial_partner_id.name.encode('ISO-8859-7')

        if inv_type_require_counterpart or (inv_type_allows_counterpart and partner_not_from_greece):
            values.update({
                'counterpart_postal_code': self.commercial_partner_id.zip,
                'counterpart_city': (self.commercial_partner_id.city or "").encode('ISO-8859-7') or None,
            })