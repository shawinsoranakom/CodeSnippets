def test_mail_composer_content(self):
        """ Test content management (body, mail_server_id, scheduled_date,
        subject) in both comment and mass mailing mode. Template update is also
        tested.

        TDE TODO: add test for record_alias_domain_id and record_company_id """
        template_void = self.template.copy(default={
            'body_html': False,
            'mail_server_id': False,
            'scheduled_date': False,
            'subject': False,
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

                # 1. check without template + template update
                composer = self.env['mail.compose.message'].with_context(ctx).create({
                    'body': '<p>Test Body <t t-out="record.name"/></p>',
                    'mail_server_id': self.mail_server_default.id,
                    'scheduled_date': '{{ datetime.datetime(2023, 1, 10, 10, 0, 0) }}',
                    'subject': 'My amazing subject for {{ record.name }}',
                })

                # creation values are taken
                self.assertEqual(composer.body, '<p>Test Body <t t-out="record.name"/></p>')
                self.assertEqual(composer.mail_server_id, self.mail_server_default)
                self.assertEqual(composer.scheduled_date, '{{ datetime.datetime(2023, 1, 10, 10, 0, 0) }}')
                self.assertEqual(composer.subject, 'My amazing subject for {{ record.name }}')

                # changing template should update its content
                composer.write({'template_id': self.template.id})

                # values come from template
                if composition_mode == 'comment' and not batch:
                    self.assertEqual(composer.body, f'<p>TemplateBody {self.test_record.name}</p>')
                    self.assertEqual(composer.mail_server_id, self.template.mail_server_id)
                    self.assertEqual(FieldDatetime.from_string(composer.scheduled_date),
                                     self.reference_now + timedelta(days=2))
                    self.assertEqual(composer.subject, f'TemplateSubject {self.test_record.name}')
                else:
                    self.assertEqual(composer.body, self.template.body_html)
                    self.assertEqual(composer.mail_server_id, self.template.mail_server_id)
                    self.assertEqual(composer.scheduled_date, self.template.scheduled_date)
                    self.assertEqual(composer.subject, self.template.subject)

                # manual values is kept over template
                composer.write({
                    'body': '<p>Back to my amazing body <t t-out="record.name"/></p>',
                    'mail_server_id': self.mail_server_default.id,
                    'scheduled_date': '{{ datetime.datetime(2023, 1, 10, 10, 0, 0) }}',
                    'subject': 'Back to my amazing subject for {{ record.name }}',
                })
                self.assertEqual(composer.body, '<p>Back to my amazing body <t t-out="record.name"/></p>')
                self.assertEqual(composer.mail_server_id, self.mail_server_default)
                self.assertEqual(composer.scheduled_date, '{{ datetime.datetime(2023, 1, 10, 10, 0, 0) }}')
                self.assertEqual(composer.subject, 'Back to my amazing subject for {{ record.name }}')

                # update with template with void values: void value is not forced in
                # rendering mode as well as in raw mode
                composer.write({'template_id': template_void.id})

                if composition_mode == 'comment' and not batch:
                    self.assertEqual(composer.body, '<p>Back to my amazing body <t t-out="record.name"/></p>')
                    self.assertEqual(composer.mail_server_id, self.mail_server_default)
                    self.assertEqual(composer.scheduled_date, '{{ datetime.datetime(2023, 1, 10, 10, 0, 0) }}')
                    self.assertEqual(composer.subject, 'Back to my amazing subject for {{ record.name }}')
                else:
                    self.assertEqual(composer.body, '<p>Back to my amazing body <t t-out="record.name"/></p>')
                    self.assertEqual(composer.mail_server_id, self.mail_server_default)
                    self.assertEqual(composer.scheduled_date, '{{ datetime.datetime(2023, 1, 10, 10, 0, 0) }}')
                    self.assertEqual(composer.subject, 'Back to my amazing subject for {{ record.name }}')

                # reset template should reset values
                composer.write({'template_id': False})

                # values are reset with compute field
                if composition_mode == 'comment' and not batch:
                    self.assertFalse(composer.body)
                    self.assertFalse(composer.mail_server_id.id)
                    self.assertFalse(composer.scheduled_date)
                    self.assertEqual(composer.subject, self.test_record._message_compute_subject())
                    self.assertIn(f'Ticket for {self.test_record.name}', composer.subject,
                                  'Check effective content')
                else:
                    self.assertFalse(composer.body)
                    self.assertFalse(composer.mail_server_id.id)
                    self.assertFalse(composer.scheduled_date)
                    self.assertFalse(composer.subject)

                # 2. check with default
                ctx['default_template_id'] = self.template.id
                composer = self.env['mail.compose.message'].with_context(ctx).create({
                    'template_id': self.template.id,
                })

                # values come from template
                if composition_mode == 'comment' and not batch:
                    self.assertEqual(composer.body, f'<p>TemplateBody {self.test_record.name}</p>')
                    self.assertEqual(composer.mail_server_id, self.template.mail_server_id)
                    self.assertEqual(FieldDatetime.from_string(composer.scheduled_date), self.reference_now + timedelta(days=2))
                    self.assertEqual(composer.subject, f'TemplateSubject {self.test_record.name}')
                else:
                    self.assertEqual(composer.body, self.template.body_html)
                    self.assertEqual(composer.mail_server_id, self.template.mail_server_id)
                    self.assertEqual(composer.scheduled_date, self.template.scheduled_date)
                    self.assertEqual(composer.subject, self.template.subject)

                # 3. check at create
                ctx.pop('default_template_id')
                composer = self.env['mail.compose.message'].with_context(ctx).create({
                    'template_id': self.template.id,
                })

                # values come from template
                if composition_mode == 'comment' and not batch:
                    self.assertEqual(composer.body, f'<p>TemplateBody {self.test_record.name}</p>')
                    self.assertEqual(composer.mail_server_id, self.template.mail_server_id)
                    self.assertEqual(FieldDatetime.from_string(composer.scheduled_date), self.reference_now + timedelta(days=2))
                    self.assertEqual(composer.subject, f'TemplateSubject {self.test_record.name}')
                else:
                    self.assertEqual(composer.body, self.template.body_html)
                    self.assertEqual(composer.mail_server_id, self.template.mail_server_id)
                    self.assertEqual(composer.scheduled_date, self.template.scheduled_date)
                    self.assertEqual(composer.subject, self.template.subject)

                # 4. template + user input
                ctx['default_template_id'] = self.template.id
                composer = self.env['mail.compose.message'].with_context(ctx).create({
                    'body': '<p>Test Body</p>',
                    'mail_server_id': False,
                    'scheduled_date': '{{ datetime.datetime(2023, 1, 10, 10, 0, 0) }}',
                    'subject': 'My amazing subject',
                })

                # creation values are taken
                self.assertEqual(composer.body, '<p>Test Body</p>')
                self.assertEqual(composer.mail_server_id.id, False)
                self.assertEqual(composer.scheduled_date, '{{ datetime.datetime(2023, 1, 10, 10, 0, 0) }}')
                self.assertEqual(composer.subject, 'My amazing subject')