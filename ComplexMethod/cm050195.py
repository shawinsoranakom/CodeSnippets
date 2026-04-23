def test_mail_composer_author(self):
        """ Test author_id / email_from synchronization, in both comment and mass
        mail modes. """
        template_void = self.template.copy(default={
            'email_from': False,
        })

        for composition_mode, batch_mode in product(('comment', 'mass_mail'),
                                                    (False, True, 'domain')):
            with self.subTest(composition_mode=composition_mode, batch_mode=batch_mode):
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

                composer = self.env['mail.compose.message'].with_context(ctx).create({
                    'body': '<p>Test Body</p>',
                })

                # default values are current user
                self.assertEqual(composer.author_id, self.env.user.partner_id)
                self.assertEqual(composer.composition_mode, composition_mode)
                self.assertEqual(composer.email_from, self.env.user.email_formatted)

                # author update should reset email (FIXME: currently not synchronized)
                composer.write({'author_id': self.partner_1})
                self.assertEqual(composer.author_id, self.partner_1)
                self.assertEqual(composer.email_from, self.env.user.email_formatted,
                                 'MailComposer: TODO: author / email_from are not synchronized')
                # self.assertEqual(composer.email_from, self.partner_1.email_formatted)

                # changing template should update its email_from
                composer.write({'template_id': self.template.id})

                if composition_mode == 'comment' and not batch:
                    self.assertEqual(composer.author_id, self.test_record.user_id.partner_id,
                                     f'MailComposer: should try to link in rendered mode: {composer.author_id.name}, expected {self.env.user.name}')
                    self.assertEqual(composer.email_from, self.test_record.user_id.email_formatted,
                                     'MailComposer: should take email_from rendered from template')
                else:
                    self.assertEqual(composer.author_id, self.env.user.partner_id,
                                     f'MailComposer: should reset to current user in raw mode: {composer.author_id.name}, expected {self.env.user.name}')
                    self.assertEqual(composer.email_from, self.template.email_from,
                                     'MailComposer: should take email_from raw from template')

                # manual values are kept over template values; if email does not
                # match any author, reset author
                composer.write({'email_from': self.test_from})
                if composition_mode == 'comment' and not batch:
                    self.assertEqual(composer.author_id, self.test_record.user_id.partner_id,
                                     'MailComposer: TODO: compute not called')
                    self.assertEqual(composer.email_from, self.test_from,
                                     'MailComposer: manual values should be kept')
                else:
                    self.assertEqual(composer.author_id, self.env.user.partner_id,
                                     'MailComposer: TODO: compute not called')
                    self.assertEqual(composer.email_from, self.test_from,
                                     'MailComposer: manual values should be kept')

                # Update with template with void email_from field, should result in reseting email_from to a default value
                # rendering mode as well as when copying template values
                composer.write({'template_id': template_void.id})

                if composition_mode == 'comment' and not batch:
                    self.assertEqual(composer.author_id, self.env.user.partner_id,
                                     'MailComposer: TODO: author / email_from are not synchronized')
                    self.assertEqual(composer.email_from, self.env.user.email_formatted)
                else:
                    self.assertEqual(composer.author_id, self.env.user.partner_id,
                                     'MailComposer: TODO: author / email_from are not synchronized')
                    self.assertEqual(composer.email_from, self.env.user.email_formatted)

                # reset template: values are reset due to call to default_get
                composer.write({'template_id': False})

                if composition_mode == 'comment' and not batch:
                    self.assertEqual(composer.author_id, self.env.user.partner_id,
                                     'MailComposer: TODO: author / email_from are not synchronized')
                    self.assertEqual(composer.email_from, self.env.user.email_formatted)
                else:
                    self.assertEqual(composer.author_id, self.env.user.partner_id,
                                     'MailComposer: TODO: author / email_from are not synchronized')
                    self.assertEqual(composer.email_from, self.env.user.email_formatted)