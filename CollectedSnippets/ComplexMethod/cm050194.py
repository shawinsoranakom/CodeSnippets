def test_mail_composer_attachments(self):
        """ Test attachments management in both comment and mass mail mode. """
        attachment_data = self._generate_attachments_data(3, self.template._name, self.template.id)
        self.template.write({
            'attachment_ids': [(0, 0, a) for a in attachment_data],
            'report_template_ids': [(6, 0, (self.test_report + self.test_report_2).ids)],
        })
        template_void = self.template.copy(default={
            'attachment_ids': False,
            'report_template_ids': False,
        })
        attachs = self.env['ir.attachment'].sudo().search([('name', 'in', [a['name'] for a in attachment_data])])
        self.assertEqual(len(attachs), 3)
        extra_attach = self.env['ir.attachment'].create({
            'datas': base64.b64encode(b'ExtraData'),
            'mimetype': 'text/plain',
            'name': 'ExtraAttFileName.txt',
            'res_model': False,
            'res_id': False,
        })

        for composition_mode, batch_mode in product(('comment', 'mass_mail'),
                                                    (False, True, 'domain')):
            with self.subTest(composition_mode=composition_mode, batch_mode=batch_mode):
                batch = bool(batch_mode)
                test_records = self.test_records if batch else self.test_record
                ctx = {
                    'default_model': test_records._name,
                    'default_composition_mode': composition_mode,
                    'default_template_id': self.template.id,
                }
                if batch_mode == 'domain':
                    ctx['default_res_domain'] = [('id', 'in', test_records.ids)]
                else:
                    ctx['default_res_ids'] = test_records.ids

                composer = self.env['mail.compose.message'].with_context(ctx).create({
                    'body': '<p>Test Body</p>',
                })

                # values coming from template: attachment_ids + report in comment
                if composition_mode == 'comment' and not batch:
                    self.assertEqual(len(composer.attachment_ids), 5)
                    for attach in attachs:
                        self.assertIn(attach, composer.attachment_ids)
                    generated = composer.attachment_ids - attachs
                    self.assertEqual(len(generated), 2, 'MailComposer: should have 2 additional attachments for reports')
                    self.assertEqual(
                        sorted(generated.mapped('name')),
                        sorted([f'TestReport for {self.test_record.name}.html', f'TestReport2 for {self.test_record.name}.html']))
                    self.assertEqual(generated.mapped('res_model'), ['mail.compose.message'] * 2)
                    self.assertEqual(generated.mapped('res_id'), [0] * 2)
                # values coming from template: attachment_ids only (report is dynamic)
                else:
                    self.assertEqual(
                        sorted(composer.attachment_ids.ids),
                        sorted(attachs.ids)
                    )

                # manual update
                composer.write({
                    'attachment_ids': [(4, extra_attach.id)],
                })
                if composition_mode == 'comment' and not batch:
                    self.assertEqual(composer.attachment_ids, attachs + extra_attach + generated)
                else:
                    self.assertEqual(composer.attachment_ids, attachs + extra_attach)

                # update with template with void values: values are kept, void
                # value is not forced in rendering mode as well as when copying
                # template values
                composer.write({'template_id': template_void.id})

                if composition_mode == 'comment' and not batch:
                    self.assertEqual(composer.attachment_ids, attachs + extra_attach + generated)
                else:
                    self.assertEqual(composer.attachment_ids, attachs + extra_attach)

                # reset template: values are reset
                composer.write({'template_id': False})
                if composition_mode == 'comment' and not batch:
                    self.assertFalse(composer.attachment_ids)
                else:
                    self.assertFalse(composer.attachment_ids)