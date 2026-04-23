def _get_vat_required_valid(self, company=None):
        # OVERRIDE
        # If VIES validation does not apply to this partner (e.g. they
        # are in the same country as the partner), then skip.
        vat_required_valid = super()._get_vat_required_valid(company=company)
        if (
            company and company.country_id and self.with_company(company).perform_vies_validation
            and ('EU' in company.country_id.country_group_codes or self.country_id and self.country_id.has_foreign_fiscal_position)
        ):
            vat_required_valid = vat_required_valid and self.vies_valid
        return vat_required_valid