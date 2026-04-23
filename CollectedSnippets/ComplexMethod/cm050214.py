def test_mail_mail_send_server_attachment_to_download_link(self, mock_attachment_file_size):
        """ Test that when the mail size exceeds the max email size limit,
        attachments are turned into download links added at the end of the
        email content.

        The feature is tested in the following conditions:
        - using a specified server or the default one (to test command ICP parameter)
        - in batch mode
        - with mail that exceed (with one or more attachments) or not the limit
        - with attachment owned by a business record or not: attachments not owned by a
        business record are never turned into links because their lifespans are not
        controlled by the user (might even be deleted right after the message is sent).
        """
        def count_attachments(message):
            if isinstance(message, str):
                return 0
            elif message.is_multipart():
                return sum(count_attachments(part) for part in message.get_payload())
            elif 'attachment' in message.get('Content-Disposition', ''):
                return 1
            return 0

        mock_attachment_file_size.return_value = 1024 * 128
        # Define some constant to ease the understanding of the test
        test_mail_server = self.mail_server_domain_2
        max_size_always_exceed = 0.1
        max_size_never_exceed = 10

        for n_attachment, mail_server, business_attachment, expected_is_links in (
                # 1 attachment which doesn't exceed max size
                (1, self.env['ir.mail_server'], True, False),
                # 3 attachment: exceed max size
                (3, self.env['ir.mail_server'], True, True),
                # 1 attachment: exceed max size
                (1, self.env['ir.mail_server'], True, True),
                # Same as above with a specific server. Note that the default and server max_email size are reversed.
                (1, test_mail_server, True, False),
                (3, test_mail_server, True, True),
                (1, test_mail_server, True, True),
                # Attachments not linked to a business record are never turned to link
                (3, self.env['ir.mail_server'], False, False),
                (1, test_mail_server, False, False),
        ):
            # Setup max email size to check that the right maximum is used (default or mail server one)
            if expected_is_links:
                max_size_test_succeed = max_size_always_exceed * n_attachment
                max_size_test_fail = max_size_never_exceed
            else:
                max_size_test_succeed = max_size_never_exceed
                max_size_test_fail = max_size_always_exceed * n_attachment
            if mail_server:
                self.env['ir.config_parameter'].sudo().set_param('base.default_max_email_size', max_size_test_fail)
                mail_server.max_email_size = max_size_test_succeed
            else:
                self.env['ir.config_parameter'].sudo().set_param('base.default_max_email_size', max_size_test_succeed)

            attachments = self.env['ir.attachment'].sudo().create([{
                'name': f'attachment{idx_attachment}',
                'res_name': 'test',
                'res_model': self.test_record._name if business_attachment else 'mail.message',
                'res_id': self.test_record.id if business_attachment else 0,
                'datas': 'IA==',  # a non-empty base64 content. We mock attachment file_size to simulate bigger size.
            } for idx_attachment in range(n_attachment)])
            with self.mock_smtplib_connection():
                mails = self.env['mail.mail'].create([{
                    'attachment_ids': attachments.ids,
                    'body_html': '<p>Test</p>',
                    'email_from': 'test@test_2.com',
                    'email_to': f'mail_{mail_idx}@test.com',
                } for mail_idx in range(2)])
                mails._send(mail_server=mail_server)

            self.assertEqual(len(self.emails), 2)
            for outgoing_email in self.emails:
                message_raw = outgoing_email['message']
                message_parsed = message_from_string(message_raw)
                message_cleaned = re.sub(r'[\s=]', '', message_raw)
                with self.subTest(n_attachment=n_attachment, mail_server=mail_server,
                                  business_attachment=business_attachment, expected_is_links=expected_is_links):
                    if expected_is_links:
                        self.assertEqual(count_attachments(message_parsed), 0,
                                         'Attachments should have been removed (replaced by download links)')
                        self.assertTrue(all(attachment.access_token for attachment in attachments),
                                        'Original attachment should have been modified (access_token added)')
                        self.assertTrue(all(attachment.access_token in message_cleaned for attachment in attachments),
                                         'All attachments should have been turned into download links')
                    else:
                        self.assertEqual(count_attachments(message_parsed), n_attachment,
                                         'All attachments should be present')
                        self.assertEqual(message_cleaned.count('access_token'), 0,
                                         'Attachments should not have been turned into download links')
                        self.assertTrue(all(not attachment.access_token for attachment in attachments),
                                        'Original attachment should not have been modified (access_token not added)')