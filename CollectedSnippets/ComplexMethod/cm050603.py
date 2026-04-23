def _get_validity_errors(self, company, partner, currency):
        """
        Check whether all declarations of intent in self are valid for the specified `company`, `partner`, `date` and `currency'.
        Violating these constraints leads to errors in the feature. They should not be ignored.
        Return all errors as a list of strings.
        """
        errors = []
        for declaration in self:
            if not company or declaration.company_id != company:
                errors.append(_("The Declaration of Intent belongs to company %(declaration_company)s, not %(company)s.",
                                declaration_company=declaration.company_id.name, company=company.name))
            if not currency or declaration.currency_id != currency:
                errors.append(_("The Declaration of Intent uses currency %(declaration_currency)s, not %(currency)s.",
                                declaration_currency=declaration.currency_id.name, currency=currency.name))
            if not partner or declaration.partner_id != partner.commercial_partner_id:
                errors.append(_("The Declaration of Intent belongs to partner %(declaration_partner)s, not %(partner)s.",
                                declaration_partner=declaration.partner_id.name, partner=partner.commercial_partner_id.name))
        return errors