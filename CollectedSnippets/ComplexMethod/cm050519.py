def test_task_creation_notifies_author(self):
        """ Check auto acknowledgment mail sent at new task. It should notify
        task creator, based on stage template. """
        internal_followers = self.user_projectuser.partner_id + self.user_projectmanager.partner_id
        new_partner_email = '"New Author" <new.author@test.agrolait.com>'

        incoming_cc = f'"New Cc" <new.cc@test.agrolait.com>, {self.partner_2.email_formatted}'
        incoming_to = f'{self.project_followers_alias.alias_full_name}, {self.partner_1.email_formatted}, "New Customer" <new.customer@test.agrolait.com>'
        incoming_to_filtered = f'{self.partner_1.email_formatted}, "New Customer" <new.customer@test.agrolait.com>'
        for test_user in (self.user_employee, self.user_portal, False):
            with self.subTest(user_name=test_user.name if test_user else new_partner_email):
                email_from = test_user.email_formatted if test_user else new_partner_email
                with self.mock_mail_gateway():
                    task = self.format_and_process(
                        MAIL_TEMPLATE, email_from,
                        incoming_to,
                        cc=incoming_cc,
                        subject=f'Test from {email_from}',
                        target_model='project.task',
                    )
                    self.flush_tracking()

                if test_user:
                    author = test_user.partner_id
                else:
                    author = self.env['res.partner'].search([('email_normalized', '=', 'new.author@test.agrolait.com')])
                    self.assertTrue(author, 'Project automatically creates a partner for incoming email')
                    self.assertEqual(author.email, 'new.author@test.agrolait.com', 'Should parse name/email correctly')
                    self.assertEqual(author.name, 'New Author', 'Should parse name/email correctly')

                # do not converts Cc into partners, used only to populate email_cc field
                new_partner_cc = self.env['res.partner'].search([('email_normalized', '=', 'new.cc@test.agrolait.com')])
                self.assertFalse(new_partner_cc)
                # do not convert other people in To, simply recognized if they exist
                new_partner_customer = self.env['res.partner'].search([('email_normalized', '=', 'new.customer@test.agrolait.com')])
                self.assertFalse(new_partner_customer)

                self.assertIn('Please call me as soon as possible', task.description)
                self.assertEqual(task.email_cc, f'"New Cc" <new.cc@test.agrolait.com>, {self.partner_2.email_formatted}, {self.partner_1.email_formatted}, "New Customer" <new.customer@test.agrolait.com>')
                self.assertEqual(task.name, f'Test from {author.email_formatted}')
                self.assertEqual(task.partner_id, author)
                self.assertEqual(task.project_id, self.project_followers)
                self.assertEqual(task.stage_id, self.project_followers.type_ids[0])
                # followers: email cc is added in followers at creation time, aka only recognized partners
                self.assertEqual(task.message_partner_ids, internal_followers + author + self.partner_1 + self.partner_2)
                # messages
                self.assertEqual(len(task.message_ids), 2)
                # first message: incoming email: sent to email followers
                incoming_email = task.message_ids[1]
                self.assertMailNotifications(
                    incoming_email,
                    [
                        {
                            'content': 'Please call me as soon as possible',
                            'message_type': 'email',
                            'message_values': {
                                'author_id': author,
                                'email_from': formataddr((author.name, author.email_normalized)),
                                # coming from incoming email
                                'incoming_email_cc': incoming_cc,
                                'incoming_email_to': incoming_to_filtered,
                                'mail_server_id': self.env['ir.mail_server'],
                                # followers of 'new task' subtype (but not original To as they
                                # already received the email)
                                'notified_partner_ids': internal_followers,
                                # deduced from 'To' and 'Cc' (recognized partners)
                                'partner_ids': self.partner_1 + self.partner_2,
                                'parent_id': self.env['mail.message'],
                                'reply_to': formataddr((author.name, self.project_followers_alias.alias_full_name)),
                                'subject': f'Test from {author.email_formatted}',
                                'subtype_id': self.env.ref('project.mt_task_new'),
                            },
                            'notif': [
                                {'partner': self.user_projectmanager.partner_id, 'type': 'inbox',},
                                {'partner': self.user_projectuser.partner_id, 'type': 'email',},
                            ],
                        },
                    ],
                )

                # second message: acknowledgment: sent to email author
                acknowledgement = task.message_ids[0]
                # task created by odoobot if not incoming user -> odoobot author of ack email
                acknowledgement_author = test_user.partner_id if test_user else self.partner_root
                self.assertMailNotifications(
                    acknowledgement,
                    [
                        {
                            'content': f'Hello {author.name}',
                            'message_type': 'auto_comment',
                            'message_values': {
                                'author_id': acknowledgement_author,
                                'email_from': acknowledgement_author.email_formatted,
                                'incoming_email_cc': False,
                                'incoming_email_to': False,
                                'mail_server_id': self.env['ir.mail_server'],
                                # default recipients: partner_id, no note followers
                                'notified_partner_ids': author,
                                # default recipients: partner_id
                                'partner_ids': author,
                                'parent_id': incoming_email,
                                'reply_to': formataddr((acknowledgement_author.name, self.project_followers_alias.alias_full_name)),
                                'subject': f'Test Acknowledge {task.name}',
                                # defined by _track_template
                                'subtype_id': self.env.ref('mail.mt_note'),
                            },
                            'notif': [
                                # specific email for portal customer, due to portal mixin
                                {'partner': author, 'type': 'email', 'group': 'portal_customer',},
                            ],
                        },
                    ],
                )

                # uses Chatter: fetches suggested recipients, post a message
                # - checks all suggested: email_cc field, primary email
                # ------------------------------------------------------------
                suggested_all = task.with_user(self.user_projectuser)._message_get_suggested_recipients(
                    reply_discussion=True, no_create=False,
                )
                new_partner_cc = self.env['res.partner'].search(
                    [('email_normalized', '=', 'new.cc@test.agrolait.com')]
                )
                self.assertEqual(new_partner_cc.email, 'new.cc@test.agrolait.com')
                self.assertEqual(new_partner_cc.name, 'New Cc')
                new_partner_customer = self.env['res.partner'].search(
                    [('email_normalized', '=', 'new.customer@test.agrolait.com')]
                )
                self.assertEqual(new_partner_customer.email, 'new.customer@test.agrolait.com')
                self.assertEqual(new_partner_customer.name, 'New Customer')
                expected_all = []
                if not test_user:
                    expected_all = [
                        {  # last message recipient is proposed
                            'create_values': {},
                            'email': 'new.author@test.agrolait.com',
                            'name': 'New Author',
                            'partner_id': author.id,  # already created by project upon initial email reception
                        }
                    ]
                elif test_user == self.user_portal:
                    expected_all = [
                        {  # customer is proposed, even if follower, because shared
                            'create_values': {},
                            'email': self.user_portal.email_normalized,
                            'name': self.user_portal.name,
                            'partner_id': self.user_portal.partner_id.id,
                        }
                    ]
                expected_all += [
                    {  # mail.thread.cc: email_cc field
                        'create_values': {},
                        'email': 'new.cc@test.agrolait.com',
                        'name': 'New Cc',
                        'partner_id': new_partner_cc.id,
                    },
                    {  # incoming email other recipients (new.customer)
                        'create_values': {},
                        'email': 'new.customer@test.agrolait.com',
                        'name': 'New Customer',
                        'partner_id': new_partner_customer.id,
                    },
                    # other CC (partner_2) and customer (partner_id) already follower
                ]
                for suggested, expected in zip(suggested_all, expected_all, strict=True):
                    self.assertDictEqual(suggested, expected)

                # finally post the message with recipients
                with self.mock_mail_gateway():
                    recipients = new_partner_cc + new_partner_customer
                    if not test_user:
                        recipients += author
                    responsible_answer = task.with_user(self.user_projectuser).message_post(
                        body='<p>Well received !',
                        partner_ids=recipients.ids,
                        message_type='comment',
                        subject=f'Re: {task.name}',
                        subtype_id=self.env.ref('mail.mt_comment').id,
                    )
                self.assertEqual(task.message_partner_ids, internal_followers + author + self.partner_1 + self.partner_2)

                external_partners = self.partner_1 + self.partner_2 + new_partner_cc + new_partner_customer
                self.assertMailNotifications(
                    responsible_answer,
                    [
                        {
                            'content': 'Well received !',
                            'mail_mail_values': {
                                'mail_server_id': self.env['ir.mail_server'],  # no specified server
                            },
                            'message_type': 'comment',
                            'message_values': {
                                'author_id': self.user_projectuser.partner_id,
                                'email_from': self.user_projectuser.partner_id.email_formatted,
                                'incoming_email_cc': False,
                                'incoming_email_to': False,
                                'mail_server_id': self.env['ir.mail_server'],
                                # projectuser not notified of its own message, even if follower
                                'notified_partner_ids': self.user_projectmanager.partner_id + author + external_partners,
                                'parent_id': incoming_email,
                                # coming from post
                                'partner_ids': recipients,
                                'reply_to': formataddr((self.user_projectuser.name, self.project_followers_alias.alias_full_name)),
                                'subject': f'Re: {task.name}',
                                'subtype_id': self.env.ref('mail.mt_comment'),
                            },
                            'notif': [
                                # original author has a specific email with links and tokens
                                {'partner': author, 'type': 'email', 'group': 'portal_customer'},
                                {'partner': self.partner_1, 'type': 'email'},
                                {'partner': self.partner_2, 'type': 'email'},
                                {'partner': new_partner_cc, 'type': 'email'},
                                {'partner': new_partner_customer, 'type': 'email'},
                                {'partner': self.user_projectmanager.partner_id, 'type': 'inbox'},
                            ],
                        },
                    ],
                )

                # SMTP emails really sent (not Inbox guy then)
                # expected Msg['To'] : Reply-All behavior: actual recipient, then
                # all "not internal partners" and catchall (to receive answers)
                for partner in (responsible_answer.notified_partner_ids - self.user_projectmanager.partner_id):
                    exp_msg_to_partners = partner | external_partners
                    if author != self.user_employee.partner_id:  # external only !
                        exp_msg_to_partners |= author
                    exp_msg_to = exp_msg_to_partners.mapped('email_formatted')
                    with self.subTest(name=partner.name):
                        self.assertSMTPEmailsSent(
                            mail_server=self.mail_server_notification,
                            msg_from=formataddr((self.user_projectuser.name, f'{self.default_from}@{self.alias_domain}')),
                            smtp_from=self.mail_server_notification.from_filter,
                            smtp_to_list=[partner.email_normalized],
                            msg_to_lst=exp_msg_to,
                        )

                # customer replies using "Reply All" + adds new people
                # ------------------------------------------------------------
                self.gateway_mail_reply_from_smtp_email(
                    MAIL_TEMPLATE, [author.email_normalized], reply_all=True,
                    cc=f'"Another Cc" <another.cc@test.agrolait.com>, {self.partner_3.email}',
                    target_model='project.task',
                )
                self.assertEqual(
                    task.email_cc,
                    '"Another Cc" <another.cc@test.agrolait.com>, valid.poilboeuf@gmail.com, "New Cc" <new.cc@test.agrolait.com>, '
                    '"Valid Poilvache" <valid.other@gmail.com>, "Valid Lelitre" <valid.lelitre@agrolait.com>, "New Customer" <new.customer@test.agrolait.com>',
                    'Updated with new Cc')
                self.assertEqual(len(task.message_ids), 4, 'Incoming email + acknowledgement + chatter reply + customer reply')
                self.assertEqual(
                    task.message_partner_ids,
                    internal_followers + author + self.partner_1 + self.partner_2 + self.partner_3 + new_partner_cc + new_partner_customer,
                    'Project adds recognized recipients as followers')

                self.assertMailNotifications(
                    task.message_ids[0],
                    [
                        {
                            'content': 'Please call me as soon as possible',
                            'message_type': 'email',
                            'message_values': {
                                'author_id': author,
                                'email_from': author.email_formatted,
                                # coming from incoming email
                                'incoming_email_cc': f'"Another Cc" <another.cc@test.agrolait.com>, {self.partner_3.email}',
                                # To: received email Msg-To - customer who replies, without email Reply-To
                                'incoming_email_to': ', '.join(external_partners.mapped('email_formatted')),
                                'mail_server_id': self.env['ir.mail_server'],
                                # notified: followers - already emailed, aka internal only
                                'notified_partner_ids': internal_followers,
                                'parent_id': responsible_answer,
                                # same reasoning as email_to/cc
                                'partner_ids': external_partners + self.partner_3,
                                'reply_to': formataddr((author.name, self.project_followers_alias.alias_full_name)),
                                'subject': f'Re: Re: {task.name}',
                                'subtype_id': self.env.ref('mail.mt_comment'),
                            },
                            'notif': [
                                {'partner': self.user_projectuser.partner_id, 'type': 'email',},
                                {'partner': self.user_projectmanager.partner_id, 'type': 'inbox',},
                            ],
                        },
                    ],
                )

                # clear for other loops
                (new_partner_cc + new_partner_customer).unlink()