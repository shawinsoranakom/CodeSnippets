def test_mail_composer_wtpl_recipients_email_fields(self):
        """ Test various combinations of corner case / not standard filling of
        email fields: multi email, formatted emails, ... on template, used to
        post a message using the composer."""
        existing_partners = self.env['res.partner'].search([])
        partner_format_tofind, partner_multi_tofind, partner_at_tofind = self.env['res.partner'].create([
            {
                'email': '"FindMe Format" <find.me.format@test.example.com>',
                'name': 'FindMe Format',
            }, {
                'email': 'find.me.multi.1@test.example.com, "FindMe Multi" <find.me.multi.2@test.example.com>',
                'name': 'FindMe Multi',
            }, {
                'email': '"Bike@Home" <find.me.at@test.example.com>',
                'name': 'NotBike@Home',
            }
        ])
        email_ccs = ['"Raoul" <test.cc.1@example.com>', '"Raoulette" <test.cc.2@example.com>', 'test.cc.2.2@example.com>', 'invalid', '  ']
        email_tos = ['"Micheline, l\'Immense" <test.to.1@example.com>', 'test.to.2@example.com', 'wrong', '  ']

        self.template.write({
            'email_cc': ', '.join(email_ccs),
            'email_from': '{{ user.email_formatted }}',
            'email_to': ', '.join(email_tos + (partner_format_tofind + partner_multi_tofind + partner_at_tofind).mapped('email')),
            'partner_to': f'{self.partner_1.id},{self.partner_2.id},0,test',
        })
        self.user_employee.write({'email': 'email.from.1@test.mycompany.com, email.from.2@test.mycompany.com'})
        self.partner_1.write({'email': '"Valid Formatted" <valid.lelitre@agrolait.com>'})
        self.partner_2.write({'email': 'valid.other.1@agrolait.com, valid.other.cc@agrolait.com'})
        # ensure values used afterwards for testing
        self.assertEqual(
            self.partner_employee.email_formatted,
            '"Ernest Employee" <email.from.1@test.mycompany.com,email.from.2@test.mycompany.com>',
            'Formatting: wrong formatting due to multi-email')
        self.assertEqual(
            self.partner_1.email_formatted,
            '"Valid Lelitre" <valid.lelitre@agrolait.com>',
            'Formatting: avoid wrong double encapsulation')
        self.assertEqual(
            self.partner_2.email_formatted,
            '"Valid Poilvache" <valid.other.1@agrolait.com,valid.other.cc@agrolait.com>',
            'Formatting: wrong formatting due to multi-email')

        # instantiate composer, post message
        composer_form = Form(self.env['mail.compose.message'].with_context(
            self._get_web_context(
                self.test_record,
                add_web=True,
                default_template_id=self.template.id,
            )
        ))
        composer = composer_form.save()
        with self.mock_mail_gateway(mail_unlink_sent=False), self.mock_mail_app():
            composer.action_send_mail()

        # find partners created during sending (as emails are transformed into partners)
        # FIXME: currently email finding based on formatted / multi emails does
        # not work
        new_partners = self.env['res.partner'].search([]).search([('id', 'not in', existing_partners.ids)])
        self.assertEqual(len(new_partners), 9,
                         'Mail (FIXME): multiple partner creation due to formatted / multi emails: 1 extra partner')
        self.assertIn(partner_format_tofind, new_partners)
        self.assertIn(partner_multi_tofind, new_partners)
        self.assertIn(partner_at_tofind, new_partners)
        self.assertEqual(new_partners[0:3].ids, (partner_format_tofind + partner_multi_tofind + partner_at_tofind).ids)
        self.assertEqual(
            sorted(new_partners.mapped('email')),
            sorted(['"Bike@Home" <find.me.at@test.example.com>',
                    '"FindMe Format" <find.me.format@test.example.com>',
                    'find.me.multi.1@test.example.com, "FindMe Multi" <find.me.multi.2@test.example.com>',
                    'find.me.multi.2@test.example.com',
                    'test.cc.1@example.com',
                    'test.cc.2@example.com',
                    'test.cc.2.2@example.com',
                    'test.to.1@example.com',
                    'test.to.2@example.com']),
            'Mail: created partners for valid emails (wrong / invalid not taken into account) + did not find corner cases (FIXME)'
        )
        self.assertEqual(
            sorted(new_partners.mapped('email_formatted')),
            sorted(['"NotBike@Home" <find.me.at@test.example.com>',
                    '"FindMe Format" <find.me.format@test.example.com>',
                    '"FindMe Multi" <find.me.multi.1@test.example.com,find.me.multi.2@test.example.com>',
                    '"find.me.multi.2@test.example.com" <find.me.multi.2@test.example.com>',
                    '"test.cc.1@example.com" <test.cc.1@example.com>',
                    '"test.cc.2@example.com" <test.cc.2@example.com>',
                    '"test.cc.2.2@example.com" <test.cc.2.2@example.com>',
                    '"test.to.1@example.com" <test.to.1@example.com>',
                    '"test.to.2@example.com" <test.to.2@example.com>']),
        )
        self.assertEqual(
            sorted(new_partners.mapped('name')),
            sorted(['NotBike@Home',
                    'FindMe Format',
                    'FindMe Multi',
                    'find.me.multi.2@test.example.com',
                    'test.cc.1@example.com',
                    'test.to.1@example.com',
                    'test.to.2@example.com',
                    'test.cc.2@example.com',
                    'test.cc.2.2@example.com']),
            'Mail: currently setting name = email, not taking into account formatted emails'
        )

        # global outgoing: two mail.mail (all customer recipients, then all employee recipients)
        # and 11 emails, and 1 inbox notification (admin)
        # FIXME template is sent only to partners (email_to are transformed) ->
        #   wrong / weird emails (see email_formatted of partners) is kept
        # FIXME: more partners created than real emails (see above) -> due to
        #   transformation from email -> partner in template 'generate_recipients'
        #   there are more partners than email to notify;
        self.assertEqual(len(self._new_mails), 2, 'Should have created 2 mail.mail')
        self.assertEqual(
            len(self._mails), len(new_partners) + 3,
            f'Should have sent {len(new_partners) + 3} emails, one / recipient ({len(new_partners)} mailed partners + partner_1 + partner_2 + partner_employee)')
        self.assertMailMail(
            self.partner_employee_2, 'sent',
            author=self.partner_employee,
            email_values={
                'body_content': f'TemplateBody {self.test_record.name}',
                # single email event if email field is multi-email
                'email_from': formataddr((self.user_employee.name, 'email.from.1@test.mycompany.com')),
                'subject': f'TemplateSubject {self.test_record.name}',
            },
            fields_values={
                # currently holding multi-email 'email_from'
                'email_from': formataddr((self.user_employee.name, 'email.from.1@test.mycompany.com,email.from.2@test.mycompany.com')),
            },
            mail_message=self.test_record.message_ids[0],
        )
        recipients = self.partner_1 + self.partner_2 + new_partners
        self.assertMailMail(
            recipients,
            'sent',
            author=self.partner_employee,
            email_to_recipients=[
                [self.partner_1.email_formatted],
                [f'"{self.partner_2.name}" <valid.other.1@agrolait.com>', f'"{self.partner_2.name}" <valid.other.cc@agrolait.com>'],
            ] + [[new_partners[0]['email_formatted']],
                 ['"FindMe Multi" <find.me.multi.1@test.example.com>', '"FindMe Multi" <find.me.multi.2@test.example.com>']
            ] + [[email] for email in new_partners[2:].mapped('email_formatted')],
            email_values={
                'body_content': f'TemplateBody {self.test_record.name}',
                # single email event if email field is multi-email
                'email_from': formataddr((self.user_employee.name, 'email.from.1@test.mycompany.com')),
                'subject': f'TemplateSubject {self.test_record.name}',
            },
            fields_values={
                # currently holding multi-email 'email_from'
                'email_from': formataddr((self.user_employee.name, 'email.from.1@test.mycompany.com,email.from.2@test.mycompany.com')),
            },
            mail_message=self.test_record.message_ids[0],
        )
        # actual emails sent through smtp
        for recipient in recipients:
            # multi emails -> send multiple emails (smart)
            if recipient == self.partner_2:
                smtp_to_list = ['valid.other.1@agrolait.com', 'valid.other.cc@agrolait.com']
            # find.me.format
            elif recipient == new_partners[0]:
                self.assertEqual(recipient, partner_format_tofind)
                smtp_to_list = ['find.me.format@test.example.com']
            # find.me.multi was split into two partners
            elif recipient == new_partners[1]:
                self.assertEqual(recipient, partner_multi_tofind)
                smtp_to_list = ['find.me.multi.1@test.example.com', 'find.me.multi.2@test.example.com']
            elif recipient == new_partners[3]:
                smtp_to_list = ['find.me.multi.2@test.example.com']
            # bike@home: name is not recognized as email anymore
            elif recipient == new_partners[2]:
                self.assertEqual(recipient, partner_at_tofind)
                smtp_to_list = ['find.me.at@test.example.com']
            else:
                smtp_to_list = [recipient.email_normalized]
            self.assertSMTPEmailsSent(
                smtp_from=f'{self.alias_bounce}@{self.alias_domain}',
                smtp_to_list=smtp_to_list,
                mail_server=self.mail_server_domain,
                # msg_from takes only first found normalized email to make a valid email_from
                message_from=formataddr(
                    (self.user_employee.name,
                    'email.from.1@test.mycompany.com',
                )),
                # similar envelope, assertSMTPEmailsSent cannot distinguish
                # records (would have to dive into content, too complicated)
                emails_count=1,
            )