def test_mail_composer_wtpl_complete(self):
        """ Test a composer in mass mode with a quite complete template, containing
        notably email-based recipients and attachments.

        Translations and email layout supported are also tested.
        """
        # as we use the email queue, don't have failing tests due to other outgoing emails
        self.env['mail.mail'].sudo().search([]).unlink()

        attachment_data = self._generate_attachments_data(2, self.template._name, self.template.id)
        email_to_1 = 'test.to.1@test.example.com'
        email_to_2 = 'test.to.2@test.example.com'
        email_to_3 = 'test.to.1@test.example.com'  # duplicate: should not sent twice the email
        email_cc_1 = 'test.cc.1@test.example.com'
        self.template.write({
            'auto_delete': False,  # keep sent emails to check content
            'attachment_ids': [(0, 0, a) for a in attachment_data],
            'email_to': '%s, %s, %s' % (email_to_1, email_to_2, email_to_3),
            'email_cc': email_cc_1,
            'partner_to': '%s, {{ object.customer_id.id if object.customer_id else "" }}' % self.partner_admin.id,
            'report_template_ids': [(6, 0, self.test_report.ids)],
        })
        attachs = self.env['ir.attachment'].sudo().search([('name', 'in', [a['name'] for a in attachment_data])])
        self.assertEqual(len(attachs), 2)

        # ensure initial data
        self.assertEqual(self.test_records.user_id, self.user_employee_2)
        self.assertEqual(self.test_records.message_partner_ids, self.partner_employee_2)

        for use_domain, scheduled_date, email_layout_xmlid, reply_to, use_lang in product(
            (False, True),
            (False, '{{ (object.create_date or datetime.datetime(2022, 12, 26, 18, 0, 0)) + datetime.timedelta(days=2) }}'),
            (False, 'mail.test_layout'),
            (False, '{{ ctx.get("custom_reply_to") or "info@test.example.com" }}'),
            (False, True),
        ):
            with self.subTest(use_domain=use_domain,
                              scheduled_date=scheduled_date,
                              email_layout_xmlid=email_layout_xmlid,
                              reply_to=reply_to,
                              use_lang=use_lang):
                # update test configuration
                self.template.write({
                    'reply_to': reply_to,
                    'scheduled_date': scheduled_date,
                })
                if use_lang:
                    langs = ('es_ES', 'en_US')
                    self.test_partners[0].lang = langs[0]
                    self.test_partners[1].lang = langs[1]
                else:
                    langs = (False, False)
                    self.test_partners.lang = False

                ctx = {
                    'default_model': self.test_records._name,
                    'default_composition_mode': 'mass_mail',
                    'default_template_id': self.template.id,
                    # just to check template dynamic code evaluation (see reply_to above)
                    'custom_reply_to': 'custom.reply.to@test.example.com',
                }
                if use_domain:
                    ctx['default_res_domain'] = [('id', 'in', self.test_records.ids)]
                    ctx['default_force_send'] = True  # otherwise domain = email queue
                else:
                    ctx['default_res_ids'] = self.test_records.ids
                if email_layout_xmlid:
                    ctx['default_email_layout_xmlid'] = email_layout_xmlid

                # launch composer in mass mode
                composer_form = Form(self.env['mail.compose.message'].with_context(ctx))
                composer = composer_form.save()

                # ensure some parameters used afterwards
                author = self.partner_employee
                self.assertEqual(composer.author_id, author,
                                 'Author is not synchronized, as template email_from does not match existing partner')
                self.assertEqual(composer.email_from, self.template.email_from)

                with self.mock_mail_gateway(mail_unlink_sent=False), \
                     self.mock_datetime_and_now(self.reference_now):
                    composer._action_send_mail()

                    # partners created from raw emails
                    new_partners = self.env['res.partner'].search([
                        ('email', 'in', [email_to_1, email_to_2, email_to_3, email_cc_1])
                    ])
                    self.assertEqual(len(new_partners), 3)
                    self.assertEqual(new_partners.mapped('lang'), ['en_US'] * 3,
                                     'New partners lang is always the default DB one, whatever the context')

                    # check global outgoing
                    self.assertEqual(len(self._new_mails), 2, 'Should have created 1 mail.mail per record')
                    if not scheduled_date:
                        # emails sent directly
                        self.assertEqual(len(self._mails), 10, 'Should have sent emails')
                        self.assertEqual(self._new_mails.mapped('scheduled_date'),
                                         [False] * 2)
                    else:
                        # emails not sent due to scheduled_date
                        self.assertEqual(len(self._mails), 0, 'Should not send emails, scheduled in the future')
                        self.assertEqual(self._new_mails.mapped('scheduled_date'),
                                         [self.reference_now + timedelta(days=2)] * 2)

                        # simulate cron queue at right time for sending
                        with self.mock_datetime_and_now(self.reference_now + timedelta(days=2)):
                            self.env['mail.mail'].sudo().process_email_queue()

                        # everything should be sent now
                        self.assertEqual(len(self._mails), 10, 'Should have sent 5 emails per record')

                # check email content
                for record, exp_lang in zip(self.test_records, langs):
                    # message copy is kept
                    message = record.message_ids[0]

                    if exp_lang == 'es_ES':
                        exp_body = f'SpanishBody for {record.name}'
                        exp_subject = f'SpanishSubject for {record.name}'
                    else:
                        exp_body = f'TemplateBody {record.name}'
                        exp_subject = f'TemplateSubject {record.name}'
                    if reply_to:
                        exp_reply_to = 'custom.reply.to@test.example.com'
                    else:
                        exp_reply_to = formataddr((
                            author.name,
                            f'{self.alias_catchall}@{self.alias_domain}',
                        ))
                    # template is sent only to partners (email_to are transformed)
                    self.assertMailMail(record.customer_id + new_partners + self.partner_admin,
                                        'sent',
                                        mail_message=message,
                                        author=author,
                                        email_values={
                                            'attachments_info': [
                                                {'name': 'AttFileName_00.txt', 'raw': b'AttContent_00', 'type': 'text/plain'},
                                                {'name': 'AttFileName_01.txt', 'raw': b'AttContent_01', 'type': 'text/plain'},
                                                {'name': 'TestReport for %s.html' % record.name, 'type': 'text/plain'},
                                            ],
                                            'body_content': exp_body,
                                            'email_from': self.partner_employee_2.email_formatted,
                                            # profit from this test to check references are set to message_id in mailing emails
                                            'references_message_id_check': True,
                                            'reply_to': exp_reply_to,
                                            'subject': exp_subject,
                                        },
                                        fields_values={
                                            'email_from': self.partner_employee_2.email_formatted,
                                            'mail_server_id': self.mail_server_domain,
                                            'reply_to': exp_reply_to,
                                            'reply_to_force_new': bool(reply_to),
                                            'subject': exp_subject,
                                        },
                                       )

                    # Low-level checks on outgoing email for the recipient to
                    # check layouting and language. Note that standard layout
                    # is not tested against translations, only the custom one
                    # to ease translations checks.
                    sent_mail = self._find_sent_email(
                        self.partner_employee_2.email_formatted,
                        [formataddr((record.customer_id.name, email_normalize(record.customer_id.email, strict=False)))]
                    )
                    debug_info = ''
                    if not sent_mail:
                        debug_info = '-'.join('From: %s-To: %s' % (mail['email_from'], mail['email_to']) for mail in self._mails)
                    self.assertTrue(
                        bool(sent_mail),
                        f'Expected mail from {self.partner_employee_2.email_formatted} to {formataddr((record.customer_id.name, record.customer_id.email))} not found in {debug_info}'
                    )
                    if record == self.test_records[0]:
                        self.assertEqual(sent_mail['email_to'], ['"Partner_0" <test_partner_0@example.com>'],
                                         'Should take email normalized in to')
                    else:
                        self.assertEqual(sent_mail['email_to'], ['"Partner_1" <test_partner_1@example.com>'],
                                         'Should take email normalized in to')

                    if not email_layout_xmlid:
                        self.assertEqual(
                            sent_mail['body'],
                            f'<p>{exp_body}</p>'
                        )
                    else:
                        exp_layout_content_en = 'English Layout for Ticket-like model'
                        exp_layout_content_es = 'Spanish Layout para Spanish Model Description'
                        exp_button_en = 'View Ticket-like model'
                        exp_button_es = 'Spanish Layout para Spanish Model Description'
                        if exp_lang == 'es_ES':
                            self.assertIn(exp_layout_content_es, sent_mail['body'])
                            self.assertIn(exp_button_es, sent_mail['body'])
                        else:
                            self.assertIn(exp_layout_content_en, sent_mail['body'])
                            # self.assertIn(exp_button_es, sent_mail['body'])
                            self.assertIn(exp_button_en, sent_mail['body'])