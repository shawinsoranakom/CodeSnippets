def _iap_enrich_from_response(self, iap_response):
        """ Handle from the service and enrich the lead accordingly

        :param iap_response: dict{lead_id: company data or False}
        """
        for lead in self.search([('id', 'in', list(iap_response.keys()))]):  # handle unlinked data by performing a search
            iap_data = iap_response.get(str(lead.id))
            if not iap_data:
                lead.write({'iap_enrich_done': True})
                lead.message_post_with_source(
                    'crm_iap_enrich.mail_message_lead_enrich_notfound',
                    subtype_xmlid='mail.mt_note',
                )
                continue

            values = {'iap_enrich_done': True}
            lead_fields = ['partner_name', 'reveal_id', 'street', 'city', 'zip']
            iap_fields = ['name', 'clearbit_id', 'location', 'city', 'postal_code']
            for lead_field, iap_field in zip(lead_fields, iap_fields):
                if not lead[lead_field] and iap_data.get(iap_field):
                    values[lead_field] = iap_data[iap_field]

            if not lead.phone and iap_data.get('phone_numbers'):
                values['phone'] = iap_data['phone_numbers'][0]
            if not lead.country_id and iap_data.get('country_code'):
                country = self.env['res.country'].search([('code', '=', iap_data['country_code'].upper())])
                values['country_id'] = country.id
            else:
                country = lead.country_id
            if not lead.state_id and country and iap_data.get('state_code'):
                state = self.env['res.country.state'].search([
                    ('code', '=', iap_data['state_code']),
                    ('country_id', '=', country.id)
                ])
                values['state_id'] = state.id

            lead.write(values)

            template_values = iap_data
            template_values['flavor_text'] = _("Lead enriched based on email address")
            lead.message_post_with_source(
                'iap_mail.enrich_company',
                render_values=template_values,
                subtype_xmlid='mail.mt_note',
            )