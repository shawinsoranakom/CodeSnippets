def test_composer_lang_template_comment(self):
        """ When posting in comment mode, content is rendered using the lang
        field of template. Notification layout lang is the one from the
        customer to personalize the context. When not found it fallbacks
        on rendered template lang or environment lang. """
        test_record = self.test_records[0].with_user(self.env.user)
        test_template = self.test_template.with_user(self.env.user)

        for partner in self.env['res.partner'] + self.partner_1 + self.partner_2:
            with self.subTest(partner=partner):
                test_record.write({
                    'customer_id': partner.id,
                })
                with self.mock_mail_gateway():
                    test_record.message_post_with_source(
                        test_template,
                        email_layout_xmlid='mail.test_layout',
                        message_type='comment',
                        subtype_id=self.env.ref('mail.mt_comment').id,
                    )

                # expected languages: content depend on template (lang field) aka
                # customer.lang or record.lang (see template); notif lang is
                # partner lang or default DB lang
                exp_content_lang = partner.lang if partner.lang else 'es_ES'
                exp_notif_lang = partner.lang if partner.lang else 'en_US'

                if partner:
                    customer = partner
                else:
                    customer = self.env['res.partner'].search([('email_normalized', '=', 'test.record.1@test.customer.com')], limit=1)
                    self.assertTrue(customer, 'Template usage should have created a contact based on record email')
                self.assertEqual(customer.lang, exp_notif_lang)

                customer_email = self._find_sent_email_wemail(customer.email_formatted)
                self.assertTrue(customer_email)
                body = customer_email['body']
                # check content: depends on object.lang / object.customer_id.lang
                if exp_content_lang == 'en_US':
                    self.assertIn(f'EnglishBody for {test_record.name}', body,
                                  'Body based on template should be translated')
                else:
                    self.assertIn(f'SpanishBody for {test_record.name}', body,
                                  'Body based on template should be translated')
                # check subject
                if exp_content_lang == 'en_US':
                    self.assertEqual(f'EnglishSubject for {test_record.name}', customer_email['subject'],
                                     'Subject based on template should be translated')
                else:
                    self.assertEqual(f'SpanishSubject for {test_record.name}', customer_email['subject'],
                                     'Subject based on template should be translated')
                # check notification layout content: depends on customer lang
                if exp_notif_lang == 'en_US':
                    self.assertNotIn('Spanish Layout para', body, 'Layout translation failed')
                    self.assertIn('English Layout for Lang Chatter Model', body,
                                  'Layout / model translation failed')
                    self.assertNotIn('Spanish Model Description', body, 'Model translation failed')
                    # check notification layout strings
                    self.assertNotIn('SpanishView Spanish Model Description', body,
                                     '"View document" translation failed')
                    self.assertIn(f'View {test_record._description}', body,
                                  '"View document" translation failed')
                else:
                    self.assertNotIn('English Layout for', body, 'Layout translation failed')
                    self.assertIn('Spanish Layout para Spanish Model Description', body,
                                  'Layout / model translation failed')
                    self.assertNotIn('Lang Chatter Model', body, 'Model translation failed')
                    # check notification layout strings
                    self.assertIn('SpanishView Spanish Model Description', body,
                                  '"View document" translation failed')
                    self.assertNotIn(f'View {test_record._description}', body,
                                    '"View document" translation failed')