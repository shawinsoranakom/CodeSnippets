def _l10n_it_edi_search_partner(self, company, vat, codice_fiscale, email, destination_code=None):
        base_domain = self.env['res.partner']._check_company_domain(company)
        for domain in [vat and destination_code
                           and [('vat', 'ilike', vat), ('l10n_it_pa_index', 'ilike', destination_code)],
                       vat and [('vat', 'ilike', vat)],
                       codice_fiscale and [('l10n_it_codice_fiscale', 'in', ('IT' + codice_fiscale, codice_fiscale))],
                       email and ['|', ('email', '=', email), ('l10n_it_pec_email', '=', email)]]:
            if domain and (partner := self.env['res.partner'].search(domain + base_domain, limit=1)):
                return partner
        return self.env['res.partner']