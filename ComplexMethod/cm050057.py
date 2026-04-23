def _import_partner(self, company_id, name, phone, email, vat, *, peppol_eas=False, peppol_endpoint=False, postal_address={}, **kwargs):
        """ Retrieve the partner, if no matching partner is found, create it (only if he has a vat and a name) """
        logs = []
        if peppol_eas and peppol_endpoint:
            domain = [('peppol_eas', '=', peppol_eas), ('peppol_endpoint', '=', peppol_endpoint)]
        else:
            domain = False
        partner = self.env['res.partner'] \
            .with_company(company_id) \
            ._retrieve_partner(name=name, phone=phone, email=email, vat=vat, domain=domain)
        country_code = postal_address.get('country_code')
        country = self.env['res.country'].search([('code', '=', country_code.upper())]) if country_code else self.env['res.country']
        state_code = postal_address.get('state_code')
        state = self.env['res.country.state'].search(
            [('country_id', '=', country.id), ('code', '=', state_code)],
            limit=1,
        ) if state_code and country else self.env['res.country.state']
        if not partner and name and vat:
            partner_vals = {'name': name, 'email': email, 'phone': phone, 'is_company': True}
            if peppol_eas and peppol_endpoint:
                partner_vals.update({'peppol_eas': peppol_eas, 'peppol_endpoint': peppol_endpoint})
            partner = self.env['res.partner'].create(partner_vals)
            if vat:
                partner.vat, _country_code = self.env['res.partner']._run_vat_checks(country, vat, validation='setnull')
            logs.append(_("Could not retrieve a partner corresponding to '%s'. A new partner was created.", name))
        elif not partner and not logs:
            logs.append(_("Could not retrieve partner with details: Name: %(name)s, Vat: %(vat)s, Phone: %(phone)s, Email: %(email)s",
                  name=name, vat=vat, phone=phone, email=email))
        if not partner.country_id and not partner.street and not partner.street2 and not partner.city and not partner.zip and not partner.state_id:
            partner.write({
                'country_id': country.id,
                'street': postal_address.get('street'),
                'street2': postal_address.get('additional_street'),
                'city': postal_address.get('city'),
                'zip': postal_address.get('zip'),
                'state_id': state.id,
            })
        return partner, logs