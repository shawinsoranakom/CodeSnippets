def _create_leads_batch(self, lead_type='lead', count=10, email_dup_count=0,
                            partner_count=0, partner_ids=None, user_ids=None,
                            country_ids=None, probabilities=None, suffix='', additional_lead_values=defaultdict(None)):
        """ Helper tool method creating a batch of leads, useful when dealing
        with batch processes. Please update me.

        :param string type: 'lead', 'opportunity', 'mixed' (lead then opp),
          None (depends on configuration);
        :param partner_count: if not partner_ids is given, generate partner count
          customers; other leads will have no customer;
        :param partner_ids: a set of partner ids to cycle when creating leads;
        :param user_ids: a set of user ids to cycle when creating leads;

        :return: create leads
        """
        types = ['lead', 'opportunity']
        leads_data = [{
            'name': f'TestLead{suffix}_{x:04d}',
            'type': lead_type if lead_type else types[x % 2],
            'priority': '%s' % (x % 3),
            **additional_lead_values,
        } for x in range(count)]

        # generate customer information
        partners = []
        if partner_count:
            partners = self.env['res.partner'].create([{
                'name': 'AutoPartner_%04d' % (x),
                'email': tools.formataddr((
                    'AutoPartner_%04d' % (x),
                    'partner_email_%04d@example.com' % (x),
                )),
            } for x in range(partner_count)])

        # customer information
        if partner_ids:
            for idx, lead_data in enumerate(leads_data):
                lead_data['partner_id'] = partner_ids[idx % len(partner_ids)]
        else:
            for idx, lead_data in enumerate(leads_data):
                if partner_count and idx < partner_count:
                    lead_data['partner_id'] = partners[idx].id
                else:
                    lead_data['email_from'] = tools.formataddr((
                        'TestCustomer_%02d' % (idx),
                        'customer_email_%04d@example.com' % (idx)
                    ))

        # country + phone information
        if country_ids:
            cid_to_country = dict(
                (country.id, country)
                for country in self.env['res.country'].browse([cid for cid in country_ids if cid])
            )
            for idx, lead_data in enumerate(leads_data):
                country_id = country_ids[idx % len(country_ids)]
                country = cid_to_country.get(country_id, self.env['res.country'])
                lead_data['country_id'] = country.id
                if lead_data['country_id']:
                    lead_data['phone'] = phone_validation.phone_format(
                        '0456%04d99' % (idx),
                        country.code, country.phone_code,
                        force_format='E164')
                else:
                    lead_data['phone'] = '+32456%04d99' % (idx)

        # salesteam information
        if user_ids:
            for idx, lead_data in enumerate(leads_data):
                lead_data['user_id'] = user_ids[idx % len(user_ids)]

        # probabilities
        if probabilities:
            for idx, lead_data in enumerate(leads_data):
                lead_data['probability'] = probabilities[idx % len(probabilities)]

        # duplicates (currently only with email)
        dups_data = []
        if email_dup_count and not partner_ids:
            for lead_data in leads_data:
                if not lead_data.get('partner_id') and lead_data['email_from']:
                    dup_data = dict(lead_data)
                    dup_data['name'] = 'Duplicated-%s' % dup_data['name']
                    dups_data.append(dup_data)
                if len(dups_data) >= email_dup_count:
                    break

        return self.env['crm.lead'].create(leads_data + dups_data)