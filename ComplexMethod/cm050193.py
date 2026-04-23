def test_mail_composer_comment_attachments(self):
        """Tests that all attachments are added to the composer, static attachments
        are not duplicated and while reports are re-generated, and that intermediary
        attachments are dropped."""
        attachment_data = self._generate_attachments_data(2, self.template._name, self.template.id)
        template_1 = self.template.copy({
            'attachment_ids': [(0, 0, a) for a in attachment_data],
            'report_template_ids': [(6, 0, (self.test_report + self.test_report_2).ids)],
        })
        template_1_attachments = template_1.attachment_ids
        self.assertEqual(len(template_1_attachments), 2)
        template_2 = self.template.copy({
            'attachment_ids': False,
            'report_template_ids': [(6, 0, self.test_report.ids)],
        })

        # begins without attachments
        composer_form = Form(self.env['mail.compose.message'].with_context(
            self._get_web_context(self.test_record, add_web=True, default_attachment_ids=[])
        ))
        self.assertEqual(len(composer_form.attachment_ids), 0)

        # change template: 2 static (attachment_ids) and 2 dynamic (reports)
        composer_form.template_id = template_1
        self.assertEqual(len(composer_form.attachment_ids), 4)
        report_attachments = [att for att in composer_form.attachment_ids if att not in template_1_attachments]
        self.assertEqual(len(report_attachments), 2)
        tpl_attachments = composer_form.attachment_ids[:] - self.env['ir.attachment'].concat(*report_attachments)
        self.assertEqual(tpl_attachments, template_1_attachments)

        # change template: 0 static (attachment_ids) and 1 dynamic (report)
        composer_form.template_id = template_2
        self.assertEqual(len(composer_form.attachment_ids), 1)
        report_attachments = [att for att in composer_form.attachment_ids if att not in template_1_attachments]
        self.assertEqual(len(report_attachments), 1)
        tpl_attachments = composer_form.attachment_ids[:] - self.env['ir.attachment'].concat(*report_attachments)
        self.assertFalse(tpl_attachments)

        # change back to template 1
        composer_form.template_id = template_1
        self.assertEqual(len(composer_form.attachment_ids), 4)
        report_attachments = [att for att in composer_form.attachment_ids if att not in template_1_attachments]
        self.assertEqual(len(report_attachments), 2)
        tpl_attachments = composer_form.attachment_ids[:] - self.env['ir.attachment'].concat(*report_attachments)
        self.assertEqual(tpl_attachments, template_1_attachments)

        # reset template
        composer_form.template_id = self.env['mail.template']
        self.assertEqual(len(composer_form.attachment_ids), 0)