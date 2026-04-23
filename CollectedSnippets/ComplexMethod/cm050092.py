def _import_ubl_prepare_missing_customer_create_values(self, collected_values):
        customer_values = collected_values['customer_values']
        partner_create_values = {
            'is_company': True,
        }
        for key in ('phone', 'name', 'email', 'street', 'street2', 'zip', 'city'):
            if value := customer_values.get(key):
                partner_create_values[key] = value

        if (peppol_eas := customer_values.get('peppol_eas')) and (peppol_endpoint := customer_values.get('peppol_endpoint')):
            partner_create_values['peppol_eas'] = peppol_eas
            partner_create_values['peppol_endpoint'] = peppol_endpoint

        country = None
        if country_code := customer_values.get('country_code'):
            if country_code == 'GB':
                # While the code is gb, the xml_id is uk
                country_code = 'UK'
            country = self.env.ref(f'base.{country_code.lower()}', raise_if_not_found=False)
            if country:
                partner_create_values['country_id'] = country.id

        if vat := customer_values.get('vat'):
            partner_create_values['vat'], _country_code = self.env['res.partner']._run_vat_checks(country, vat, validation='setnull')
        return partner_create_values