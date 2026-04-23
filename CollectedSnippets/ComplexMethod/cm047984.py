def assertLeadConvertion(self, rule, registrations, partner=None, **expected):
        """ Tool method hiding details of lead value generation and check

        :param lead: lead created through automated rule;
        :param rule: event.lead.rule that created the lead;
        :param event: original event;
        :param registrations: source registrations (singleton or record set if done in batch);
        :param partner: partner on lead;
        """
        registrations = registrations.sorted('id')  # currently order is forced to id ASC
        lead = self.env['crm.lead'].sudo().search([
            ('registration_ids', 'in', registrations.ids),
            ('event_lead_rule_id', '=', rule.id)
        ])
        self.assertEqual(len(lead), 1, 'Invalid registrations -> lead creation, found %s leads where only 1 is expected.' % len(lead))
        self.assertEqual(lead.registration_ids, registrations, 'Invalid registrations -> lead creation, too much registrations on it.')
        event = registrations.event_id
        self.assertEqual(len(event), 1, 'Invalid registrations -> event assertion, all registrations should belong to same event')

        if partner is None:
            partner = self.env['res.partner']
        expected_reg_name = partner.name or registrations._find_first_notnull('name') or registrations._find_first_notnull('email')
        if partner:
            expected_contact_name = partner.name if not partner.is_company else False
            expected_partner_name = partner.name if partner.is_company else False
        else:
            expected_contact_name = registrations._find_first_notnull('name')
            expected_partner_name = False

        # event information
        self.assertEqual(lead.event_id, event)
        self.assertEqual(lead.referred, event.name)

        # registration information
        registration_phone = registrations._find_first_notnull('phone')
        self.assertEqual(lead.partner_id, partner)
        self.assertEqual(lead.name, '%s - %s' % (event.name, expected_reg_name))
        self.assertNotIn('False', lead.name)  # avoid a "Dear False" like construct ^^ (this assert is serious and intended)
        self.assertEqual(lead.contact_name, expected_contact_name)
        self.assertEqual(lead.partner_name, expected_partner_name)
        self.assertEqual(lead.email_from, partner.email if partner and partner.email else registrations._find_first_notnull('email'))
        self.assertEqual(lead.phone, partner.phone if partner and partner.phone else registration_phone)

        # description: to improve
        self.assertNotIn('False', lead.description)  # avoid a "Dear False" like construct ^^ (this assert is serious and intended)
        for registration in registrations:
            if registration.name:
                self.assertIn(registration.name, lead.description)
            elif registration.partner_id.name:
                self.assertIn(registration.partner_id.name, lead.description)
            if registration.email:
                if tools.email_normalize(registration.email) == registration.partner_id.email_normalized:
                    self.assertIn(registration.partner_id.email, lead.description)
                else:
                    self.assertIn(tools.email_normalize(registration.email), lead.description)
            if registration.phone:
                self.assertIn(registration.phone, lead.description)

        # lead configuration
        self.assertEqual(lead.type, rule.lead_type)
        self.assertEqual(lead.user_id, rule.lead_user_id)
        self.assertEqual(lead.team_id, rule.lead_sales_team_id)
        self.assertEqual(lead.tag_ids, rule.lead_tag_ids)