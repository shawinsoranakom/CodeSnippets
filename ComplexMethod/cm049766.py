def test_find_or_create_email_field(self):
        """ Test 'find_or_create' tool used in mail, notably when linking emails
        found in recipients to partners when sending emails using the mail
        composer. Test various combinations of problematic use cases like
        formatting, multi-emails, ... """
        partners = self.env['res.partner'].create([
            {
                'email': 'classic.format@test.example.com',
                'name': 'Classic Format',
            },
            {
                'email': '"FindMe Format" <find.me.format@test.example.com>',
                'name': 'FindMe Format',
            }, {
                'email': 'find.me.multi.1@test.example.com, "FindMe Multi" <find.me.multi.2@test.example.com>',
                'name': 'FindMe Multi',
            },
        ])
        # check data used for finding / searching
        self.assertEqual(
            partners.mapped('email_formatted'),
            ['"Classic Format" <classic.format@test.example.com>',
             '"FindMe Format" <find.me.format@test.example.com>',
             '"FindMe Multi" <find.me.multi.1@test.example.com,find.me.multi.2@test.example.com>']
        )
        # when having multi emails, first found one is taken as normalized email
        self.assertEqual(
            partners.mapped('email_normalized'),
            ['classic.format@test.example.com', 'find.me.format@test.example.com',
             'find.me.multi.1@test.example.com']
        )

        # classic find or create: use normalized email to compare records
        for email in ('CLASSIC.FORMAT@TEST.EXAMPLE.COM', '"Another Name" <classic.format@test.example.com>'):
            with self.subTest(email=email):
                self.assertEqual(self.env['res.partner'].find_or_create(email), partners[0])
        # find on encapsulated email: comparison of normalized should work
        for email in ('FIND.ME.FORMAT@TEST.EXAMPLE.COM', '"Different Format" <find.me.format@test.example.com>'):
            with self.subTest(email=email):
                self.assertEqual(self.env['res.partner'].find_or_create(email), partners[1])
        # multi-emails -> no normalized email -> fails each time, create new partner (FIXME)
        for email_input, match_partner in [
            ('find.me.multi.1@test.example.com', partners[2]),
            ('find.me.multi.2@test.example.com', self.env['res.partner']),
        ]:
            with self.subTest(email_input=email_input):
                partner = self.env['res.partner'].find_or_create(email_input)
                # either matching existing, either new partner
                if match_partner:
                    self.assertEqual(partner, match_partner)
                else:
                    self.assertNotIn(partner, partners)
                    self.assertEqual(partner.email, email_input)
                partner.unlink()  # do not mess with subsequent tests

        # now input is multi email -> 'parse_contact_from_email' used in 'find_or_create'
        # before trying to normalize is quite tolerant, allowing positive checks
        for email_input, match_partner, exp_email_partner in [
            ('classic.format@test.example.com,another.email@test.example.com',
              partners[0], 'classic.format@test.example.com'),  # first found email matches existing
            ('another.email@test.example.com,classic.format@test.example.com',
             self.env['res.partner'], 'another.email@test.example.com'),  # first found email does not match
            ('find.me.multi.1@test.example.com,find.me.multi.2@test.example.com',
             self.env['res.partner'], 'find.me.multi.1@test.example.com'),
        ]:
            with self.subTest(email_input=email_input):
                partner = self.env['res.partner'].find_or_create(email_input)
                # either matching existing, either new partner
                if match_partner:
                    self.assertEqual(partner, match_partner)
                else:
                    self.assertNotIn(partner, partners)
                self.assertEqual(partner.email, exp_email_partner)
                if partner not in partners:
                    partner.unlink()