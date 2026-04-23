def test_mail_composer_wtpl_complete(self):
        """ Test a posting process using a complex template, holding several
        additional recipients and attachments. It is done in monorecord and
        in batch since this is now supported.

        This tests notifies: 2 new email_to (+ 1 duplicated), 1 email_cc,
        test_records followers and partner_admin added in partner_to.

        Global notification
          * monorecord: send notifications right away (force_send=True)
          * multirecord: delay notification sending (force_send=False)

        Use cases
          * scheduled_date: creates mail.message.schedule (no email sent), then
            scheduling send notifications with notification parameters kept
          * otherwise: global behavior

        Test with and without notification layout specified.

        Test with and without languages.

        Setup with batch and langs
          * record1: customer lang=es_ES
                     follower partner_employee_2 lang=en_US
                     3 new partners (en_US) created by template
          * record2: customer lang=en_US
                     follower partner_employee_2 lang=en_US
                     3 new partners (en_US) created by template
        """
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
            'report_template_ids': [(6, 0, (self.test_report + self.test_report_2).ids)],
        })
        attachs = self.env['ir.attachment'].sudo().search([('name', 'in', [a['name'] for a in attachment_data])])
        self.assertEqual(len(attachs), 2)

        for batch_mode, scheduled_date, email_layout_xmlid, reply_to, use_lang in product(
            (False, True, 'domain'),
            (False, '{{ (object.create_date or datetime.datetime(2022, 12, 26, 18, 0, 0)) + datetime.timedelta(days=2) }}'),
            (False, 'mail.test_layout'),
            (False, '{{ ctx.get("custom_reply_to") or "info@test.example.com" }}'),
            (False, True),
        ):
            with self.subTest(batch_mode=batch_mode,
                              scheduled_date=scheduled_date,
                              email_layout_xmlid=email_layout_xmlid,
                              reply_to=reply_to,
                              use_lang=use_lang):
                # update test configuration
                batch = bool(batch_mode)
                self.template.write({
                    'scheduled_date': scheduled_date,
                    'email_layout_xmlid': email_layout_xmlid,
                    'reply_to': reply_to,
                })
                if use_lang:
                    if batch:
                        langs = ('es_ES', 'en_US')
                        self.test_partners[0].lang = langs[0]
                        self.test_partners[1].lang = langs[1]
                    else:
                        langs = ('es_ES',)
                        self.partner_1.lang = langs[0]
                if not use_lang:
                    if batch:
                        langs = (False, False)
                        self.test_partners.lang = False
                    else:
                        langs = (False,)
                        self.partner_1.lang = False
                test_records = self.test_records if batch else self.test_record

                # ensure initial data
                self.assertEqual(len(test_records.customer_id), len(test_records))
                self.assertEqual(test_records.user_id, self.user_employee_2)
                self.assertEqual(test_records.message_partner_ids, self.partner_employee_2)

                ctx = {
                    'default_model': test_records._name,
                    'default_composition_mode': 'comment',
                    'default_template_id': self.template.id,
                    # avoid successive tests issues with followers
                    'mail_post_autofollow_author_skip': True,
                    # just to check template dynamic code evaluation (see reply_to above)
                    'custom_reply_to': 'custom.reply.to@test.example.com',
                }
                if batch_mode == 'domain':
                    ctx['default_res_domain'] = [('id', 'in', test_records.ids)]
                else:
                    ctx['default_res_ids'] = test_records.ids

                # open a composer and run it in comment mode
                composer_form = Form(self.env['mail.compose.message'].with_context(ctx))
                composer = composer_form.save()
                self.assertEqual(composer.email_layout_xmlid, email_layout_xmlid)

                # ensure some parameters used afterwards
                if batch:
                    author = self.env.user.partner_id
                    self.assertEqual(composer.author_id, author,
                                     'Author cannot be synchronized with a raw email_from')
                    self.assertEqual(composer.email_from, self.template.email_from)
                else:
                    author = self.partner_employee_2
                    self.assertEqual(composer.author_id, author,
                                     'Author is synchronized with rendered email_from')
                    self.assertEqual(composer.email_from, self.partner_employee_2.email_formatted)
                if reply_to:
                    if batch:
                        self.assertEqual(composer.reply_to, '{{ ctx.get("custom_reply_to") or "info@test.example.com" }}')
                    else:
                        self.assertEqual(composer.reply_to, 'custom.reply.to@test.example.com')
                    self.assertTrue(composer.reply_to_force_new, 'Template forces reply_to -> consider it is a new thread')
                else:
                    self.assertFalse(composer.reply_to)
                    self.assertFalse(composer.reply_to_force_new)

                # due to scheduled_date, cron for sending notification will be used
                schedule_cron_id = self.env.ref('mail.ir_cron_send_scheduled_message').id
                with self.mock_mail_gateway(mail_unlink_sent=False), \
                     self.mock_mail_app(), \
                     self.mock_datetime_and_now(self.reference_now), \
                     self.capture_triggers(schedule_cron_id) as capt:
                    composer._action_send_mail()

                    # notification process should not have been sent
                    if scheduled_date:
                        self.assertFalse(self._new_mails)
                        self.assertFalse(self._mails)
                    # monorecord: force_send notifications
                    elif not batch:
                        # as there are recipients with different langs: we have
                        # 3 outgoing mails: partner_employee2 (user) then customers
                        # in two langs
                        if use_lang:
                            self.assertEqual(
                                len(self._new_mails), 3,
                                'Should have created 1 mail for user, then 2 for customers that belong to 2 langs')
                        # without lang, recipients are grouped by main usage aka user and customer
                        else:
                            self.assertEqual(
                                len(self._new_mails), 2,
                                'Should have created 1 mail for user, then 1 for customers')
                        self.assertEqual(self._new_mails.mapped('state'), ['sent'] * len(self._new_mails))
                        self.assertEqual(len(self._mails), 5, 'Should have sent 5 emails, one per recipient per record')
                    # multirecord: use email queue
                    else:
                        # see not-batch comment, then add 2 mails for the second
                        # record as all customers have same language
                        if use_lang:
                            self.assertEqual(
                                len(self._new_mails), 5,
                                'Should have created 3 mails for first record, then 2 for second')
                        else:
                            self.assertEqual(
                                len(self._new_mails), 4,
                                'Should have created 2 mails / record (one for user, one for customers)')
                        self.assertEqual(self._new_mails.mapped('state'), ['outgoing'] * len(self._new_mails))
                        self.assertEqual(len(self._mails), 0, 'Should have put emails in queue and not sent any emails')
                        # simulate cron sending emails
                        self.env['mail.mail'].sudo().process_email_queue()

                # notification process should not have been sent
                if scheduled_date:
                    self.assertEqual(
                        capt.records.mapped('call_at'), [self.reference_now + timedelta(days=2)] * len(test_records),
                        msg='Should have created a cron trigger for the scheduled sending'
                    )
                else:
                    self.assertFalse(capt.records)

                # check new partners have been created based on emails given
                new_partners = self.env['res.partner'].search([
                    ('email', 'in', [email_to_1, email_to_2, email_to_3, email_cc_1])
                ])
                self.assertEqual(len(new_partners), 3)
                self.assertEqual(
                    set(new_partners.mapped('email')),
                    {'test.to.1@test.example.com', 'test.to.2@test.example.com', 'test.cc.1@test.example.com'},
                )
                self.assertEqual(
                    set(new_partners.mapped('lang')),
                    {'en_US'},
                )

                # if scheduled_date is set: simulate cron for sending notifications
                if scheduled_date:
                    # Send the scheduled message from the CRON
                    with self.mock_mail_gateway(mail_unlink_sent=False), \
                         self.mock_mail_app(), \
                         self.mock_datetime_and_now(self.reference_now + timedelta(days=3)):
                        self.env['mail.message.schedule'].sudo()._send_notifications_cron()

                        # monorecord: force_send notifications
                        if not batch:
                            # as there are recipients with different langs: we have
                            # 3 outgoing mails: partner_employee2 (user) then customers
                            # in two langs
                            if use_lang:
                                self.assertEqual(
                                    len(self._new_mails), 3,
                                    'Should have created 1 mail for user, then 2 for customers that belong to 2 langs')
                            # without lang, recipients are grouped by main usage aka user and customer
                            else:
                                self.assertEqual(
                                    len(self._new_mails), 2,
                                    'Should have created 1 mail for user, then 1 for customers')
                            self.assertEqual(self._new_mails.mapped('state'), ['sent'] * len(self._new_mails))
                            self.assertEqual(len(self._mails), 5, 'Should have sent 5 emails, one per recipient per record')
                        # multirecord: use email queue
                        else:
                            # see not-batch comment, then add 2 mails for the second
                            # record as all customers have same language
                            if use_lang:
                                self.assertEqual(
                                    len(self._new_mails), 5,
                                    'Should have created 3 mails for first record, then 2 for second')
                            else:
                                self.assertEqual(
                                    len(self._new_mails), 4,
                                    'Should have created 2 mails / record (one for user, one for customers)')
                            self.assertEqual(self._new_mails.mapped('state'), ['outgoing'] * len(self._new_mails))
                            self.assertEqual(len(self._mails), 0, 'Should have put emails in queue and not sent any emails')
                            # simulate cron sending emails
                            self.env['mail.mail'].sudo().process_email_queue()

                # template is sent only to partners (email_to are transformed)
                for test_record, exp_lang in zip(test_records, langs):
                    message = test_record.message_ids[0]

                    # check created mail.mail and outgoing emails. In comment
                    # 2 or 3 mails are generated (due to group-based layouting):
                    # - one for recipient that is a user
                    # - one / two for recipients that are customers, one / lang
                    # Then each recipient receives its own outgoing email. See
                    # 'assertMailMail' for more details.

                    # user email (one user, one email)
                    if exp_lang == 'es_ES':
                        exp_body = f'SpanishBody for {test_record.name}'
                        exp_subject = f'SpanishSubject for {test_record.name}'
                    else:
                        exp_body = f'TemplateBody {test_record.name}'
                        exp_subject = f'TemplateSubject {test_record.name}'
                    if reply_to:
                        exp_reply_to = 'custom.reply.to@test.example.com'
                    else:
                        exp_reply_to = formataddr((
                            author.name,
                            f'{self.alias_catchall}@{self.alias_domain}'
                        ))
                    self.assertMailMail(self.partner_employee_2, 'sent',
                                        mail_message=message,
                                        author=author,  # author is different in batch and monorecord mode (raw or rendered email_from)
                                        email_values={
                                            'body_content': exp_body,
                                            'email_from': test_record.user_id.email_formatted,  # set by template
                                            'reply_to': exp_reply_to,
                                            'subject': exp_subject,
                                            'attachments_info': [
                                                {'name': 'AttFileName_00.txt', 'raw': b'AttContent_00', 'type': 'text/plain'},
                                                {'name': 'AttFileName_01.txt', 'raw': b'AttContent_01', 'type': 'text/plain'},
                                                {'name': f'TestReport for {test_record.name}.html', 'type': 'text/plain'},
                                                {'name': f'TestReport2 for {test_record.name}.html', 'type': 'text/plain'},
                                            ]
                                        },
                                        fields_values={
                                            'mail_server_id': self.mail_server_domain,
                                            'reply_to_force_new': bool(reply_to),
                                        },
                                       )

                    # customers emails (several customers, one or two emails depending
                    # on multi-lang testing environment)
                    if use_lang and test_record == test_records[0]:
                        # in this case, we are in a multi-lang customers testing
                        emails_recipients = [
                            test_record.customer_id,  # es_ES
                            new_partners  # en_US (default lang of new customers)
                        ]
                    else:
                        # all recipients have same language, one email
                        emails_recipients = [test_record.customer_id + new_partners]

                    for recipients in emails_recipients:
                        self.assertMailMail(recipients, 'sent',
                                            mail_message=message,
                                            author=author,  # author is different in batch and monorecord mode (raw or rendered email_from)
                                            email_values={
                                                'body_content': exp_body,
                                                'email_from': test_record.user_id.email_formatted,  # set by template
                                                'subject': exp_subject,
                                                'attachments_info': [
                                                    {'name': 'AttFileName_00.txt', 'raw': b'AttContent_00', 'type': 'text/plain'},
                                                    {'name': 'AttFileName_01.txt', 'raw': b'AttContent_01', 'type': 'text/plain'},
                                                    {'name': f'TestReport for {test_record.name}.html', 'type': 'text/plain'},
                                                    {'name': f'TestReport2 for {test_record.name}.html', 'type': 'text/plain'},
                                                ]
                                            },
                                            fields_values={
                                                'mail_server_id': self.mail_server_domain,
                                            },
                                           )

                    # Specifically for the language-specific recipient, perform
                    # low-level checks on outgoing email for the recipient to
                    # check layouting and language. Note that standard layout
                    # is not tested against translations, only the custom one
                    # to ease translations checks.
                    # We could do the check for other layouts but it would be
                    # mainly noisy / duplicated check
                    email = self._find_sent_email(test_record.user_id.email_formatted, [test_record.customer_id.email_formatted])
                    self.assertTrue(bool(email), 'Email not found, check recipients')

                    exp_layout_content_en = 'English Layout for Ticket-like model'
                    exp_layout_content_es = 'Spanish Layout para Spanish Model Description'
                    exp_button_en = 'View Ticket-like model'
                    exp_button_es = 'SpanishView Spanish Model Description'
                    if email_layout_xmlid:
                        if exp_lang == 'es_ES':
                            self.assertIn(exp_layout_content_es, email['body'])
                            self.assertIn(exp_button_es, email['body'])
                        else:
                            self.assertIn(exp_layout_content_en, email['body'])
                            self.assertIn(exp_button_en, email['body'])
                    else:
                        # check default layouting applies
                        if exp_lang == 'es_ES':
                            self.assertIn('html lang="es_ES"', email['body'])
                        else:
                            self.assertIn('html lang="en_US"', email['body'])

                    # message is posted and notified admin
                    self.assertEqual(message.subtype_id, self.env.ref('mail.mt_comment'))
                    self.assertNotified(message, [{'partner': self.partner_admin, 'is_read': False, 'type': 'inbox'}])
                    # attachments are copied on message and linked to document
                    self.assertEqual(
                        set(message.attachment_ids.mapped('name')),
                        set(['AttFileName_00.txt', 'AttFileName_01.txt',
                             f'TestReport for {test_record.name}.html',
                             f'TestReport2 for {test_record.name}.html'])
                    )
                    self.assertEqual(set(message.attachment_ids.mapped('res_model')), set([test_record._name]))
                    self.assertEqual(set(message.attachment_ids.mapped('res_id')), set(test_record.ids))
                    self.assertTrue(all(attach not in message.attachment_ids for attach in attachs), 'Should have copied attachments')