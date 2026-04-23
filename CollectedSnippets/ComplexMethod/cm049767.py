def test_find_or_create_from_emails(self):
        """ Test for '_find_or_create_from_emails' allowing to find or create
        partner based on emails in a batch-enabled and optimized fashion. """
        with self.mockPartnerCalls():
            partners = self.env['res.partner'].with_context(lang='en_US')._find_or_create_from_emails(
                [item[0] for item in self.samples],
                additional_values=None,
            )
        self.assertEqual(len(partners), len(self.samples))
        self.assertEqual(len(self._new_partners), len(self.samples) - 2, 'Two duplicates in samples')

        for (sample, exp_name, exp_email), partner in zip(self.samples, partners):
            # specific to '_from_emails': name used as email is no email found
            exp_email = exp_email or exp_name
            with self.subTest(sample=sample):
                self.assertFalse(partner.company_id)
                self.assertEqual(partner.email, exp_email)
                self.assertEqual(partner.email_normalized, tools.email_normalize(exp_email))
                self.assertTrue(partner.id)
                self.assertEqual(partner.lang, 'en_US')
                self.assertEqual(partner.name, exp_name)

        new_samples = self.samples + [
            # new
            ('"New Customer" <new.customer@test.EXAMPLE.com>', 'New Customer', 'new.customer@test.example.com'),
            # duplicate (see in sample)
            ('"Duplicated Raoul" <RAOUL@chirurgiens-dentistes.fr>', 'Raoul Grosbedon', 'raoul@chirurgiens-dentistes.fr'),
            # new (even if invalid)
            ('Invalid', 'Invalid', ''),
            # ignored, completely invalid
            (False, False, False),
            (None, False, False),
            (' ', False, False),
            ('', False, False),
        ]
        all_emails = [item[0] for item in new_samples]
        with self.mockPartnerCalls():
            partners = self.env['res.partner'].with_context(lang='en_US')._find_or_create_from_emails(
                all_emails,
                additional_values={
                    tools.email_normalize(email) or email: {
                        'company_id': self.env.company.id,
                    }
                    for email in all_emails if email and email.strip()
                },
            )
        self.assertEqual(len(partners), len(new_samples))
        self.assertEqual(len(self._new_partners), 2, 'Only 2 real new partners in new sample')

        for (sample, exp_name, exp_email), partner in zip(new_samples, partners):
            with self.subTest(sample=sample, exp_name=exp_name, exp_email=exp_email, partner=partner):
                # specific to '_from_emails': name used as email is no email found
                exp_email = exp_email or exp_name
                exp_company = self.env.company if sample in [
                    '"New Customer" <new.customer@test.EXAMPLE.com>',  # valid email, not known -> new customer
                    'Invalid'  # invalid email, not known -> create a new partner
                ] else self.env['res.company']
                if sample in [False, None, ' ', '']:
                    self.assertFalse(partner)
                else:
                    exp_email_normalized = tools.email_normalize(exp_email)
                    self.assertEqual(partner.company_id, exp_company)
                    self.assertEqual(partner.email_normalized, exp_email_normalized)
                    self.assertEqual(partner.name, exp_name)