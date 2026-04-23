def test_post_multi_lang_recipients(self):
        """ Test posting on a document in a multilang environment. Currently
        current user's lang determines completely language used for notification
        layout notably, when no template is involved.

        Lang layout for this test (to better check various configuration and
        check which lang wins the final output, if any)

          * current users: various between en and es;
          * partner1: es
          * partner2: en
        """
        test_records = self.test_records.with_env(self.env)
        test_records.message_subscribe(partner_ids=(self.partner_1 + self.partner_2).ids)

        for employee_lang, email_layout_xmlid in product(
            ('en_US', 'es_ES'),
            (False, 'mail.test_layout'),
        ):
            with self.subTest(employee_lang=employee_lang, email_layout_xmlid=email_layout_xmlid):
                self.user_employee.write({
                    'lang': employee_lang,
                })
                for record in test_records:
                    with self.mock_mail_gateway(mail_unlink_sent=False), \
                         self.mock_mail_app():
                        record.message_post(
                            body=Markup('<p>Hi there</p>'),
                            email_layout_xmlid=email_layout_xmlid,
                            message_type='comment',
                            subject='TeDeum',
                            subtype_xmlid='mail.mt_comment',
                        )
                        message = record.message_ids[0]
                        self.assertEqual(
                            message.notified_partner_ids, self.partner_1 + self.partner_2
                        )

                        # check created mail.mail and outgoing emails. One email
                        # is generated for each partner 'partner_1' and 'partner_2'
                        # different language thus different layout
                        for partner in self.partner_1 + self.partner_2:
                            _mail = self.assertMailMail(
                                partner, 'sent',
                                mail_message=message,
                                author=self.partner_employee,
                                email_values={
                                    'body_content': '<p>Hi there</p>',
                                    'email_from': self.partner_employee.email_formatted,
                                    'subject': 'TeDeum',
                                },
                            )

                        # Low-level checks on outgoing email for the recipient to
                        # check layouting and language. Note that standard layout
                        # is not tested against translations, only the custom one
                        # to ease translations checks.
                        for partner, exp_lang in zip(
                            self.partner_1 + self.partner_2,
                            ('en_US', 'es_ES')
                        ):
                            email = self._find_sent_email(
                                self.partner_employee.email_formatted,
                                [partner.email_formatted]
                            )
                            self.assertTrue(bool(email), 'Email not found, check recipients')
                            self.assertEqual(partner.lang, exp_lang, 'Test misconfiguration')

                            exp_layout_content_en = 'English Layout for Lang Chatter Model'
                            exp_layout_content_es = 'Spanish Layout para Spanish Model Description'
                            exp_button_en = 'View Lang Chatter Model'
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