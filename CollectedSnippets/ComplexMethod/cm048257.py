def _create_company_from_iap(self, email):
        domain = tools.email_domain_extract(email)
        iap_data = self._iap_enrich(domain)
        if 'enrichment_info' in iap_data:
            return None, iap_data['enrichment_info']

        phone_numbers = iap_data.get('phone_numbers')
        emails = iap_data.get('email')
        new_company_info = {
            'is_company': True,
            'name': iap_data.get("name") or domain,
            'street': iap_data.get("street_name"),
            'city': iap_data.get("city"),
            'zip': iap_data.get("postal_code"),
            'phone': phone_numbers[0] if phone_numbers else None,
            'website': iap_data.get("domain"),
            'email': emails[0] if emails else None
        }

        logo_url = iap_data.get('logo')
        if logo_url:
            try:
                response = requests.get(logo_url, timeout=2)
                if response.ok:
                    new_company_info['image_1920'] = base64.b64encode(response.content)
            except Exception as e:
                _logger.warning('Download of image for new company %s failed, error %s', new_company_info['name'], e)

        if iap_data.get('country_code'):
            country = request.env['res.country'].search([('code', '=', iap_data['country_code'].upper())])
            if country:
                new_company_info['country_id'] = country.id
                if iap_data.get('state_code'):
                    state = request.env['res.country.state'].search([
                        ('code', '=', iap_data['state_code']),
                        ('country_id', '=', country.id)
                    ])
                    if state:
                        new_company_info['state_id'] = state.id

        new_company_info.update({
            'iap_search_domain': self._get_iap_search_term(email),
            'iap_enrich_info': json.dumps(iap_data),
        })

        new_company = request.env['res.partner'].create(new_company_info)

        new_company.message_post_with_source(
            'iap_mail.enrich_company',
            render_values=iap_data,
            subtype_xmlid='mail.mt_note',
        )

        return new_company, {'type': 'company_created'}