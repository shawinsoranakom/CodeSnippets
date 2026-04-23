def lead_vals_from_response(self, lead_type, team_id, tag_ids, user_id, company_data, people_data):
        country_id = company_data.get('country_id')
        if not country_id:
            country_id = self.env['res.country'].search([('code', '=', company_data['country_code'])]).id
        website_url = 'https://%s' % company_data['domain'] if company_data.get('domain') else False
        lead_vals = {
            # Lead vals from record itself
            'type': lead_type,
            'team_id': team_id,
            'tag_ids': [(6, 0, tag_ids)],
            'user_id': user_id,
            'reveal_id': company_data.get('duns') or company_data.get('clearbit_id', ''),
            # Lead vals from data
            'name': company_data.get('name', '') or company_data.get('domain', ''),
            'partner_name': company_data.get('name', ''),
            'email_from': next(iter(company_data.get('email', [])), ''),
            'phone': company_data.get('phone') or next(iter(company_data.get('phone_numbers', [])), ''),
            'website': website_url,
            'street': company_data.get('street') or company_data.get('location', ''),
            'street2': company_data.get('street2'),
            'city': company_data.get('city', ''),
            'zip': company_data.get('zip') or company_data.get('postal_code', ''),
            'country_id': country_id,
            'state_id': self._find_state_id(company_data.get('state_code'), country_id),
        }

        # If type is people then add first contact in lead data
        if people_data:
            lead_vals.update({
                'contact_name': people_data[0]['full_name'],
                'email_from': people_data[0]['email'],
                'function': people_data[0]['title'],
            })
        return lead_vals