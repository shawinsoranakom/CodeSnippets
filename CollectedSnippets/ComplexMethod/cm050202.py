def test_mail_composer_duplicates(self):
        """ Ensures emails sent to the same recipient multiple times
            are only sent when they are not duplicates
        """
        # add access to Mail Template Editor
        self.user_employee.group_ids += self.env.ref('mail.group_mail_template_editor')
        # Access can also be made available to all users.
        # self.env['ir.config_parameter'].sudo().set_param('mail.restrict.template.rendering', False)

        self.template.write({
            'auto_delete': False,
            'body_html': '<p>Common Body</p>',
            'email_to': '',
            'partner_to': '{{ object.customer_id.id if object.customer_id else "" }}',
            'subject': 'Common Subject',
        })

        # Guarantee points of variation for test_report_3
        self.test_records[0].write({'count': 1, 'name': 'A'})
        self.test_records[1].write({'count': 2, 'name': 'B'})

        template_attachment, composer_attachment = self.env['ir.attachment'].create([{
            'datas': base64.b64encode(b'ExtraData'),
            'mimetype': 'text/plain',
            'name': f'{record._name}_Common_Attachment.txt',
            'res_id': record.id if record else False,
            'res_model': record._name,
        } for record in (self.template, self.env['mail.compose.message'])])

        customer_ids = self.partners[:2]
        customer_ids.write({
            'email': 'test@test.lan'
        })

        def _instanciate_composer(composer_attachments=False):
            composer_form = Form(self.env['mail.compose.message'].with_context(
                self._get_web_context(self.test_records[:2], add_web=True,
                                      default_template_id=self.template.id)
            ))
            composer = composer_form.save()
            if composer_attachments:
                composer_attachments.res_id = composer.id
                composer.attachment_ids += composer_attachments
            return composer

        base_customer_values = [{'email': 'test@test.lan'}]
        # different recipients should always receive emails
        customer_diff_emails = [{'email': f'difftest{n}@test.lan'} for n in range(2)]
        base_template_values = {
            'attachment_ids': [Command.clear()],
            'body_html': '<p>Common Body</p>',
            'report_template_ids': [Command.clear()],
            'subject': 'Common Subject',
        }
        same_attachments = {'attachment_ids': template_attachment.ids}
        diff_body = {'body_html': '<p><t t-esc="object.name"></t></p>'}
        # regardless of whether they have different bodies or not, they are considered duplicates
        diff_attachment_same_content = {'report_template_ids': [self.test_report_2.id]}
        diff_attachment_diff_content = {'report_template_ids': [self.test_report_3.id]}
        diff_subject = {'subject': '{{ object.name }}'}

        # all template variations using same recipients
        diff_combinations = product(
            [[diff_body], [diff_subject],
             [diff_attachment_same_content], [diff_attachment_diff_content],
             [diff_attachment_same_content, same_attachments],
             [diff_body, diff_attachment_diff_content, diff_subject]],
            [base_customer_values])
        # no template variations using different recipients
        diff_combinations = chain(diff_combinations, [[[], customer_diff_emails]])
        # expect all sent
        for template_changes, customer_changes in diff_combinations:
            test_template_values = dict(base_template_values)
            for change in template_changes:
                test_template_values.update(change)
            self.template.write(test_template_values)
            for customer, base_vals, update_vals in zip(customer_ids, base_customer_values, customer_changes):
                customer.write({**base_vals, **update_vals})
            with self.subTest(template_values=test_template_values, customer_changes=customer_changes):
                composer = _instanciate_composer()
                with self.mock_mail_gateway(mail_unlink_sent=False), self.mock_mail_app():
                    composer._action_send_mail()
                self.assertEqual(len(self._new_mails), 2)
                # check emails
                for record in self.test_records[:2]:
                    # email_to will be normalized and formatted, even if already formatted
                    expected_subject = base_template_values['subject']
                    if test_template_values['subject'] != base_template_values['subject']:
                        expected_subject = record.name
                    expected_body = base_template_values['body_html']
                    if test_template_values['body_html'] != base_template_values['body_html']:
                        expected_body = f'<p>{record.name}</p>'
                    expected_attachment_info = []
                    if self.template.attachment_ids:
                        expected_attachment_info.append({'name': 'mail.template_Common_Attachment.txt', 'type': 'text/plain'})
                    if self.template.report_template_ids:
                        test_report_name = 'TestReport2' if self.template.report_template_ids == self.test_report_2 else 'TestReport3'
                        expected_attachment_info.append(
                            {'name': f'{test_report_name} for {record.name}.html', 'type': 'text/plain'},
                        )
                    self.assertMailMailWEmails(
                        [record.customer_id.email],
                        'sent',
                        author=self.env.user.partner_id,
                        content=expected_body,
                        mail_message=record.message_ids[0],
                        email_to_recipients=[[record.customer_id.email_formatted]],
                        email_values={
                            'attachments_info': expected_attachment_info,
                            'body': expected_body,
                            'email_from': record.user_id.email_formatted,
                            'subject': expected_subject,
                        },
                    )

        # expect duplicates
        cases = [
            (False, []),
            (composer_attachment, []),
            ([], [same_attachments]),
            (composer_attachment, [same_attachments]),
        ]
        for composer_attachment, template_changes in cases:
            test_template_values = dict(base_template_values)
            for change in template_changes:
                test_template_values.update(change)
            self.template.write(test_template_values)
            # reset customers to have the same email
            for customer, base_vals in zip(customer_ids, base_customer_values):
                customer.write(base_vals)
            with self.subTest(composer_attachments=composer_attachment, template_values=test_template_values):
                composer = _instanciate_composer(composer_attachments=composer_attachment)
                with self.mock_mail_gateway(mail_unlink_sent=False), self.mock_mail_app():
                    composer._action_send_mail()
                self.assertEqual(len(self._new_mails), 2)
                self.assertEqual(len(self._mails), 1)
                # check email
                expected_attachment_info = []
                if template_changes:
                    expected_attachment_info.append({
                        'name': f'{self.template._name}_Common_Attachment.txt',
                        'raw': b'ExtraData',
                        'type': 'text/plain',
                    })
                if composer_attachment:
                    expected_attachment_info.append({
                        'name': f'{composer._name}_Common_Attachment.txt',
                        'raw': b'ExtraData',
                        'type': 'text/plain',
                    })
                self.assertMailMailWRecord(
                    self.test_records[0],
                    [self.test_records[0].customer_id],
                    'sent',
                    author=self.env.user.partner_id,
                    content='Common Body',
                    email_values={
                        'attachments_info': expected_attachment_info,
                        'body_content': 'Common Body',
                        'email_from': record.user_id.email_formatted,
                        'subject': 'Common Subject',
                    },
                )
                self. assertMailMailWRecord(
                    self.test_records[1],
                    [self.test_records[1].customer_id],
                    'cancel',
                    author=self.env.user.partner_id,
                    content='Common Body',
                    email_values={
                        'attachments_info': expected_attachment_info,
                        'body_content': 'Common Body',
                        'email_from': record.user_id.email_formatted,
                        'subject': 'Common Subject',
                    },
                )