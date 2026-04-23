def test_reveal(self):
        country_de = self.base_de
        state_de = self.de_state_st

        # check initial state of views
        self.assertEqual(
            self.env['crm.reveal.view'].search([('reveal_ip', 'in', ['90.80.70.60', '90.80.70.61', '90.80.70.70'])]),
            self.test_views
        )

        with self.mock_IAP_reveal(self.ip_to_rules, name_list=['Heinrich', 'Rivil', 'LidGen']):
            self.env['crm.reveal.rule']._process_lead_generation(autocommit=False)

        # check post state of views
        self.assertEqual(
            self.env['crm.reveal.view'].search([('reveal_ip', 'in', ['90.80.70.60', '90.80.70.61', '90.80.70.70'])]),
            self.env['crm.reveal.view'], 'Views should have been unlinked after completion'
        )

        self.assertEqual(len(self._new_leads), 3, 'Number of leads should match IPs addresses')
        for counter, base_name in enumerate(['Heinrich', 'Rivil', 'LidGen']):
            if counter == 2:
                rule = self.test_request_2
            else:
                rule = self.test_request_1

            lead = self._new_leads.filtered(lambda lead: lead.name == '%s GmbH - %s' % (base_name, rule.suffix))
            self.assertTrue(bool(lead))

            # mine information
            self.assertEqual(lead.type, 'lead' if rule == self.test_request_1 else 'opportunity')
            self.assertEqual(lead.tag_ids, self.test_crm_tags)
            self.assertEqual(lead.team_id, self.sales_team_1)
            self.assertEqual(lead.user_id, self.user_sales_leads if rule == self.test_request_1 else self.user_admin)
            # iap
            self.assertEqual(lead.reveal_id, '123_ClearbitID_%s' % base_name, 'Ensure reveal_id is set to clearbit ID')
            # clearbit information
            if rule == self.test_request_1:  # people-based
                self.assertEqual(lead.contact_name, 'Contact %s 0' % base_name)
            else:
                self.assertFalse(lead.contact_name)
            self.assertEqual(lead.city, 'Mönchengladbach')
            self.assertEqual(lead.country_id, country_de)
            if rule == self.test_request_1:  # people-based
                self.assertEqual(lead.email_from, 'test.contact.0@%s.example.com' % base_name,
                                 'Lead email should be the one from first contact if search_type people is given')
            else:
                self.assertEqual(lead.email_from, 'info@%s.example.com' % base_name,
                                 'Lead email should be the one from company data as there is no contact')
            if rule == self.test_request_1:  # people-based
                self.assertEqual(lead.function, 'Doing stuff')
            else:
                self.assertFalse(lead.function)
            self.assertFalse(lead.partner_id)
            self.assertEqual(lead.partner_name, '%s GmbH' % base_name)
            self.assertEqual(lead.phone, '+4930499193937')
            self.assertEqual(lead.state_id, state_de)
            self.assertEqual(lead.street, 'Mennrather Str. 123456')
            self.assertEqual(lead.website, 'https://%s.de' % base_name)
            self.assertEqual(lead.zip, '41179')