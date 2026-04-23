def test_mail_find_partner_from_emails_followers(self):
        """ Test '_mail_find_partner_from_emails' when dealing with records on
        which followers have to be found based on email. Check multi email
        and encapsulated email support. """
        # create partner just for the follow mechanism
        linked_record = self.env['res.partner'].sudo().create({'name': 'Record for followers'})
        follower_partner = self.env['res.partner'].sudo().create({
            'email': self._test_email,
            'name': 'Duplicated, follower of record',
        })
        linked_record.message_subscribe(partner_ids=follower_partner.ids)
        test_partner = self.test_partner.with_env(self.env)

        # standard test, no multi-email, to assert base behavior
        cases = [(self._test_email, True), (self._test_email, False)]
        for source, follower_check in cases:
            expected_partner = follower_partner if follower_check else test_partner
            with self.subTest(source=source, follower_check=follower_check):
                partner = self.env['res.partner']._mail_find_partner_from_emails(
                    [source], records=linked_record if follower_check else None
                )[0]
                self.assertEqual(partner, expected_partner)

        # formatted email
        encapsulated_test_email = f'"Robert Astaire" <{self._test_email}>'
        (follower_partner + test_partner).sudo().write({'email': encapsulated_test_email})
        cases = [
            (self._test_email, True),  # normalized
            (self._test_email, False),  # normalized
            (encapsulated_test_email, True),  # encapsulated, same
            (encapsulated_test_email, False),  # encapsulated, same
            (f'"AnotherName" <{self._test_email}', True),  # same normalized, other name
            (f'"AnotherName" <{self._test_email}', False),  # same normalized, other name
        ]
        for source, follower_check in cases:
            expected_partner = follower_partner if follower_check else test_partner
            with self.subTest(source=source, follower_check=follower_check):
                partner = self.env['res.partner']._mail_find_partner_from_emails(
                    [source], records=linked_record if follower_check else None
                )[0]
                self.assertEqual(partner, expected_partner,
                                'Mail: formatted email is recognized through usage of normalized email')

        # multi-email
        _test_email_2 = '"Robert Astaire" <not.alfredoastaire@test.example.com>'
        (follower_partner + test_partner).sudo().write({'email': f'{self._test_email}, {_test_email_2}'})
        cases = [
            (self._test_email, True, follower_partner),  # first email
            (self._test_email, False, test_partner),  # first email
            (_test_email_2, True, self.env['res.partner']),  # second email
            (_test_email_2, False, self.env['res.partner']),  # second email
            ('not.alfredoastaire@test.example.com', True, self.env['res.partner']),  # normalized second email in field
            ('not.alfredoastaire@test.example.com', False, self.env['res.partner']),  # normalized second email in field
            (f'{self._test_email}, {_test_email_2}', True, follower_partner),  # multi-email, both matching, depends on comparison
            (f'{self._test_email}, {_test_email_2}', False, test_partner),  # multi-email, both matching, depends on comparison
        ]
        for source, follower_check, expected_partner in cases:
            with self.subTest(source=source, follower_check=follower_check):
                partner = self.env['res.partner']._mail_find_partner_from_emails(
                    [source], records=linked_record if follower_check else None
                )[0]
                self.assertEqual(partner, expected_partner,
                                'Mail (FIXME): partial recognition of multi email through email_normalize')

        # test users with same email, priority given to current user
        # --------------------------------------------------------------
        self.user_employee.sudo().write({'email': '"Alfred Astaire" <%s>' % self.env.user.partner_id.email_normalized})
        found = self.env['res.partner']._mail_find_partner_from_emails([self.env.user.partner_id.email_formatted])
        self.assertEqual(found, [self.env.user.partner_id])