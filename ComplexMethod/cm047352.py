def _compute_same_vat_partner_id(self):
        for partner in self:
            # use _origin to deal with onchange()
            partner_id = partner._origin.id
            # active_test = False because if a partner has been deactivated you still want to raise the error,
            # so that you can reactivate it instead of creating a new one, which would lose its history.
            Partner = self.with_context(active_test=False).sudo()
            vats = [partner.vat]
            should_check_vat = partner.vat and len(partner.vat) != 1

            if should_check_vat and partner.country_id and 'EU_PREFIX' in partner.country_id.country_group_codes:
                if partner.vat[:2].isalpha():
                    vats.append(partner.vat[2:])
                else:
                    vats.append(partner.country_id.code + partner.vat)
                    if new_code := EU_EXTRA_VAT_CODES.get(partner.country_id.code):
                        vats.append(new_code + partner.vat)
            domain = [
                ('vat', 'in', vats),
            ]
            if partner.country_id:
                domain += [('country_id', 'in', [partner.country_id.id, False])]
            if partner.company_id:
                domain += [('company_id', 'in', [False, partner.company_id.id])]
            if partner_id:
                domain += [('id', '!=', partner_id), '!', ('id', 'child_of', partner_id)]
            # For VAT number being only one character, we will skip the check just like the regular check_vat

            partner.same_vat_partner_id = should_check_vat and not partner.parent_id and Partner.search(domain, limit=1)
            # check company_registry
            domain = [
                ('company_registry', '=', partner.company_registry),
                ('company_id', 'in', [False, partner.company_id.id]),
            ]
            if partner_id:
                domain += [('id', '!=', partner_id), '!', ('id', 'child_of', partner_id)]
            partner.same_company_registry_partner_id = bool(partner.company_registry) and not partner.parent_id and Partner.search(domain, limit=1)