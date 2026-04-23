def test_mail_composer_recipients(self):
        """ Test content management (partner_ids, reply_to) in both comment and
        mass mailing mode. Template update is also tested. Add some tests for
        partner creation based on unknown emails as this is part of the process. """
        base_recipients = self.partner_1 + self.partner_2
        self.template.write({
            'email_cc': 'test.cc.1@test.example.com, test.cc.2@test.example.com'
        })
        template_void = self.template.copy(default={
            'email_cc': False,
            'email_to': False,
            'partner_to': False,
            'reply_to': False,
        })

        for composition_mode, batch_mode in product(('comment', 'mass_mail'),
                                                    (False, True, 'domain')):
            with self.subTest(composition_mode=composition_mode, batch_mode=batch_mode):
                self.assertFalse(
                    self.env['res.partner'].search([
                        ('email_normalized', 'in', ['test.cc.1@test.example.com',
                                                    'test.cc.2@test.example.com'])
                    ])
                )
                self.assertEqual(self.test_record.message_partner_ids, self.partner_employee_2)

                batch = bool(batch_mode)
                test_records = self.test_records if batch else self.test_record
                ctx = {
                    'default_model': test_records._name,
                    'default_composition_mode': composition_mode,
                }
                if batch_mode == 'domain':
                    ctx['default_res_domain'] = [('id', 'in', test_records.ids)]
                else:
                    ctx['default_res_ids'] = test_records.ids

                # 1. check without template + template update
                composer = self.env['mail.compose.message'].with_context(ctx).create({
                    'body': '<p>Test Body</p>',
                    'partner_ids': base_recipients.ids,
                    'reply_to': 'my_reply_to@test.example.com',
                    'subject': 'My amazing subject',
                })

                # creation values are taken
                self.assertEqual(composer.partner_ids, base_recipients)
                self.assertEqual(composer.reply_to, 'my_reply_to@test.example.com')
                self.assertTrue(composer.reply_to_force_new, 'Forced reply_to -> consider it is not going to land in same thread')
                self.assertEqual(composer.reply_to_mode, 'new')

                # update with template with void values: void value is not forced in
                # rendering mode as well as when copying template values (and recipients
                # are not computed until sending in rendering mode)
                composer.write({'template_id': template_void.id})

                if composition_mode == 'comment':
                    self.assertEqual(composer.partner_ids, base_recipients)
                    self.assertEqual(composer.reply_to, 'my_reply_to@test.example.com')
                    self.assertTrue(composer.reply_to_force_new)
                else:
                    self.assertEqual(composer.partner_ids, base_recipients)
                    self.assertEqual(composer.reply_to, 'my_reply_to@test.example.com')
                    self.assertTrue(composer.reply_to_force_new)

                # changing template should update its content
                composer.write({'template_id': self.template.id})
                composer.flush_recordset()  # to be able to search for new partners

                new_partners = self.env['res.partner'].search(
                    [('email_normalized', 'in', ['test.cc.1@test.example.com',
                                                 'test.cc.2@test.example.com'])
                    ]
                )

                # values come from template
                if composition_mode == 'comment' and not batch:
                    self.assertEqual(len(new_partners), 2)
                    self.assertEqual(composer.partner_ids, self.partner_1 + new_partners, 'Template took customer_id as set on record')
                    self.assertEqual(composer.reply_to, 'info@test.example.com', 'Template was rendered')
                    self.assertTrue(composer.reply_to_force_new)
                else:
                    self.assertEqual(len(new_partners), 0)
                    self.assertEqual(composer.partner_ids, base_recipients, 'Mass mode: kept original values')
                    self.assertEqual(composer.reply_to, self.template.reply_to, 'Mass mode: raw template value')
                    self.assertTrue(composer.reply_to_force_new, 'Mass mode: reply_to -> consider this is for new threads')

                # manual values is kept over template
                composer.write({'partner_ids': [(5, 0), (4, self.partner_admin.id)]})
                self.assertEqual(composer.partner_ids, self.partner_admin)

                # reset template should reset values
                composer.write({'template_id': False})

                # values are reset
                if composition_mode == 'comment' and not batch:
                    self.assertFalse(composer.partner_ids)
                    self.assertFalse(composer.reply_to)
                    self.assertFalse(composer.reply_to_force_new)
                else:
                    self.assertFalse(composer.partner_ids)
                    self.assertFalse(composer.reply_to)
                    self.assertFalse(composer.reply_to_force_new)

                # 2. check with default
                ctx['default_template_id'] = self.template.id
                composer = self.env['mail.compose.message'].with_context(ctx).create({
                    'template_id': self.template.id,
                })

                # values come from template
                if composition_mode == 'comment' and not batch:
                    self.assertEqual(composer.partner_ids, self.partner_1 + new_partners)
                else:
                    self.assertFalse(composer.partner_ids)
                if composition_mode == 'comment' and not batch:
                    self.assertEqual(composer.reply_to, "info@test.example.com")
                else:
                    self.assertEqual(composer.reply_to, self.template.reply_to)
                self.assertTrue(composer.reply_to_force_new)  # note: this should be updated with reply-to
                self.assertEqual(composer.reply_to_mode, 'new')  # note: this should be updated with reply-to

                # 3. check at create
                ctx.pop('default_template_id')
                composer = self.env['mail.compose.message'].with_context(ctx).create({
                    'template_id': self.template.id,
                })

                # values come from template
                if composition_mode == 'comment' and not batch:
                    self.assertEqual(composer.partner_ids, self.partner_1 + new_partners)
                else:
                    self.assertFalse(composer.partner_ids)
                if composition_mode == 'comment' and not batch:
                    self.assertEqual(composer.reply_to, "info@test.example.com")
                else:
                    self.assertEqual(composer.reply_to, self.template.reply_to)
                self.assertTrue(composer.reply_to_force_new)
                self.assertEqual(composer.reply_to_mode, 'new')

                # 4. template + user input
                ctx['default_template_id'] = self.template.id
                composer = self.env['mail.compose.message'].with_context(ctx).create({
                    'body': '<p>Test Body</p>',
                    'partner_ids': base_recipients.ids,
                    'subject': 'My amazing subject',
                    'reply_to': False,
                })

                # creation values are taken
                self.assertEqual(composer.partner_ids, base_recipients)
                self.assertFalse(composer.reply_to)
                self.assertFalse(composer.reply_to_force_new)
                self.assertEqual(composer.reply_to_mode, 'update')

                self.env['res.partner'].search([
                    ('email_normalized', 'in', ['test.cc.1@test.example.com',
                                                'test.cc.2@test.example.com'])
                ]).unlink()