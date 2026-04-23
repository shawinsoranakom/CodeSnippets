def test_mail_composer_wtpl_mc(self):
        """ Test specific to multi-company environment, notably company propagation
        or aliases. """
        # add access to second company to avoid MC rules on ticket model
        self.env.user.company_ids = [(4, self.company_2.id)]

        # initial data
        self.assertEqual(self.env.company, self.company_admin)
        self.assertEqual(self.user_admin.company_id, self.company_admin)

        attachment_data = self._generate_attachments_data(2, self.template._name, self.template.id)
        email_to_1 = 'test.to.1@test.example.com'
        self.template.write({
            'auto_delete': False,  # keep sent emails to check content
            'attachment_ids': [(0, 0, a) for a in attachment_data],
            'email_from': False,  # use current user as author
            'email_layout_xmlid': 'mail.test_layout',
            'email_to': email_to_1,
            'mail_server_id': False,  # let it find a server
            'partner_to': '%s, {{ object.customer_id.id if object.customer_id else "" }}' % self.partner_admin.id,
        })
        attachs = self.env['ir.attachment'].sudo().search([('name', 'in', [a['name'] for a in attachment_data])])
        self.assertEqual(len(attachs), 2)

        for batch, companies, expected_companies, expected_alias_domains in [
            (False, self.company_admin, self.company_admin, self.mail_alias_domain),
            (
                True, self.company_admin + self.company_2, self.company_admin + self.company_2,
                self.mail_alias_domain + self.mail_alias_domain_c2,
            ),
        ]:
            with self.subTest(batch=batch,
                              companies=companies):
                # update test configuration
                test_records = self.test_records if batch else self.test_record
                for company, record in zip(companies, test_records):
                    record.company_id = company.id

                # open a composer and run it in comment mode
                composer = Form(self.env['mail.compose.message'].with_context(
                    default_composition_mode='comment',
                    default_force_send=True,  # force sending emails directly to check SMTP
                    default_model=test_records._name,
                    default_res_ids=test_records.ids,
                    default_template_id=self.template.id,
                    # avoid successive tests issues with followers
                    mail_post_autofollow_author_skip=True,
                )).save()
                with self.mock_mail_gateway(mail_unlink_sent=False), \
                     self.mock_mail_app():
                    composer._action_send_mail()

                new_partner = self.env['res.partner'].search([('email_normalized', '=', 'test.to.1@test.example.com')])
                self.assertEqual(len(new_partner), 1)
                # check output, company-specific values mainly for this test
                for record, exp_company, exp_alias_domain in zip(
                    test_records, expected_companies, expected_alias_domains
                ):
                    message = record.message_ids[0]
                    for recipient in [self.partner_employee_2, new_partner, record.customer_id]:
                        headers_recipients = f'{new_partner.email_formatted},{record.customer_id.email_formatted}'
                        self.assertMailMail(
                            recipient,
                            'sent',
                            author=self.partner_employee,
                            mail_message=message,
                            email_values={
                                'headers': {
                                    'Return-Path': f'{exp_alias_domain.bounce_email}',
                                    'X-Odoo-Objects': f'{record._name}-{record.id}',
                                    'X-Msg-To-Add': headers_recipients,
                                },
                                'subject': f'TemplateSubject {record.name}',
                            },
                            fields_values={
                                'headers': {
                                    'Return-Path': f'{exp_alias_domain.bounce_email}',
                                    'X-Odoo-Objects': f'{record._name}-{record.id}',
                                    'X-Msg-To-Add': headers_recipients,
                                },
                                'mail_server_id': self.env['ir.mail_server'],
                                'record_alias_domain_id': exp_alias_domain,
                                'record_company_id': exp_company,
                                'subject': f'TemplateSubject {record.name}',
                            },
                        )
                        smtp_to_list = [recipient.email_normalized]
                        if exp_alias_domain == self.mail_alias_domain:
                            self.assertSMTPEmailsSent(
                                smtp_from=f'{self.default_from}@{self.alias_domain}',
                                smtp_to_list=smtp_to_list,
                                mail_server=self.mail_server_notification,
                                emails_count=1,
                            )
                        else:
                            self.assertSMTPEmailsSent(
                                smtp_from=exp_alias_domain.bounce_email,
                                smtp_to_list=smtp_to_list,
                                emails_count=1,
                            )