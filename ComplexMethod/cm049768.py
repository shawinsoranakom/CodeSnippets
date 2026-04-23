def test_find_or_create_from_emails_dupes_email_field(self):
        """ Specific test for duplicates management: based on email to avoid
        creating similar partners. """
        # all same partner, same email 'test.customer@test.dupe.example.com'
        email_dupes_samples = [
            '"Formatted Customer" <test.customer@TEST.DUPE.EXAMPLE.COM>',
            'test.customer@test.dupe.example.com',
            '"Another Name" <test.customer@TEST.DUPE.EXAMPLE.COM>',
            '"Mix of both" <test.customer@test.dupe.EXAMPLE.COM',
        ]
        email_expected_name = "Formatted Customer"  # first found email will setup partner info
        email_expected_email = 'test.customer@test.dupe.example.com'  # normalized version of given email
        # all same partner, same invalid email 'test.customer.invalid.email'
        name_dupes_samples = [
            'test.customer.invalid.email',
            'test.customer.invalid.email',
        ]
        name_expected_name = 'test.customer.invalid.email'  # invalid email kept as both name and email
        name_expected_email = 'test.customer.invalid.email'  # invalid email kept as both name and email

        partners = self.env['res.partner']
        for samples, (expected_name, expected_email) in [
            (email_dupes_samples, (email_expected_name, email_expected_email)),
            (name_dupes_samples, (name_expected_name, name_expected_email)),
        ]:
            with self.subTest(samples=samples, expected_name=expected_name, expected_email=expected_email):
                with self.mockPartnerCalls():
                    partner_list = self.env['res.partner'].with_context(lang='en_US')._find_or_create_from_emails(
                        samples,
                        additional_values=None,
                    )
                # calls
                self.assertEqual(self._mock_partner_create.call_count, 1)
                self.assertEqual(self._mock_partner_search.call_count, 1)
                self.assertEqual(len(self._new_partners), 1)
                # results
                self.assertEqual(len(partner_list), len(samples))
                self.assertTrue(len(set(partner.id for partner in partner_list)) == 1 and partner_list[0].id, 'Should have a unique new partner')
                for partner in partner_list:
                    self.assertEqual(partner.email, expected_email)
                    self.assertEqual(partner.name, expected_name)

                partners += partner_list[0]

        self.assertEqual(len(partners), 2,
                         'Should have created one partner for valid email, one for invalid email')

        new_samples = [
            '"Another Customer" <test.different.1@TEST.DUPE.EXAMPLE.COM',  # actually a new valid email
            '"First Duplicate" <test.customer@TEST.DUPE.example.com',  # duplicated of valid email created above
            'test.customer.invalid.email',  # duplicate of an invalid email created above
            # multi email
            '"Multi Email Another" <TEST.different.1@test.dupe.example.com>, other.customer@other.example.com',
            '"Multi Email" <other.customer.2@test.dupe.example.com>, test.different.1@test.dupe.example.com',
            'Invalid, Multi Format other.customer.😊@test.dupe.example.com, "A Name" <yt.another.customer@new.example.com>',
            '"Unicode Formatted" <other.customer.😊@test.dupe.example.com>',  # duplicate of above
        ]
        expected = [
            (False, "Another Customer", "test.different.1@test.dupe.example.com"),
            (partners[0], "Formatted Customer", "test.customer@test.dupe.example.com"),
            (partners[1], "test.customer.invalid.email", "test.customer.invalid.email"),
            # multi email support
            (False, "Another Customer", "test.different.1@test.dupe.example.com"),
            (False, "Multi Email", "other.customer.2@test.dupe.example.com"),
            (False, "Multi Format", "other.customer.😊@test.dupe.example.com"),
            (False, "Multi Format", "other.customer.😊@test.dupe.example.com"),
        ]
        with self.mockPartnerCalls():
            new_partners = self.env['res.partner'].with_context(lang='en_US')._find_or_create_from_emails(
                new_samples,
                additional_values=None,
            )
        # calls
        self.assertEqual(self._mock_partner_create.call_count, 1)
        self.assertEqual(self._mock_partner_search.call_count, 1,
                         'Search once, even with both normalized and invalid emails')
        self.assertEqual(len(self._new_partners), 3)
        self.assertEqual(
            sorted(self._new_partners.mapped('email')),
            sorted(['other.customer.2@test.dupe.example.com',
                    'other.customer.😊@test.dupe.example.com',
                    'test.different.1@test.dupe.example.com']))
        # results
        self.assertEqual(len(new_partners), len(new_samples))
        for partner, (expected_partner, expected_name, expected_email) in zip(new_partners, expected):
            with self.subTest(partner=partner, expected_name=expected_name):
                if expected_partner:
                    self.assertEqual(partner, expected_partner)
                else:
                    self.assertIn(partner, self._new_partners)
                self.assertEqual(partner.email, expected_email)
                self.assertEqual(partner.name, expected_name)

        no_new_samples = [
            # only duplicates
            '"Another Duplicate" <test.different.1@TEST.DUPE.EXAMPLE.COM',
            '"First Duplicate2" <test.customer@TEST.DUPE.example.com',
            # falsy values
            '"Falsy" <falsy>',
            'falsy',
            '  ',
        ]
        expected = [
            (new_partners[0], "Another Customer", "test.different.1@test.dupe.example.com"),
            (partners[0], "Formatted Customer", "test.customer@test.dupe.example.com"),
            (False, '"Falsy" <falsy>', '"Falsy" <falsy>'),
            (False, "falsy", "falsy"),
            (False, False, False),
        ]
        with self.mockPartnerCalls():
            no_new_partners = self.env['res.partner'].with_context(lang='en_US')._find_or_create_from_emails(
                no_new_samples,
                additional_values=None,
            )
        # calls
        self.assertEqual(self._mock_partner_create.call_count, 1)
        self.assertEqual(self._mock_partner_search.call_count, 1)
        self.assertEqual(len(self._new_partners), 2)
        self.assertEqual(sorted(self._new_partners.mapped('email')), ['"Falsy" <falsy>', "falsy"])
        for partner, (expected_partner, expected_name, expected_email) in zip(no_new_partners, expected):
            with self.subTest(partner=partner, expected_name=expected_name):
                if expected_partner:
                    self.assertEqual(partner, expected_partner)
                elif not expected_name and not expected_email:
                    self.assertEqual(partner, self.env['res.partner'])
                else:
                    self.assertIn(partner, self._new_partners)
                self.assertEqual(partner.email, expected_email)
                self.assertEqual(partner.name, expected_name)