def _notify_members(self, message):
        """Send the given message to all members of the mail group (except the author)."""
        self.ensure_one()

        if message.mail_group_id != self:
            raise UserError(_('The group of the message do not match.'))

        if not message.mail_message_id.reply_to:
            _logger.error('The alias or the catchall domain is missing, group might not work properly.')

        base_url = self.get_base_url()
        body = self.env['mail.render.mixin']._replace_local_links(message.body)

        # Email added in a dict to be sure to send only once the email to each address
        member_emails = {
            email_normalize(member.email): member.email
            for member in self.member_ids
        }

        batch_size = int(self.env['ir.config_parameter'].sudo().get_param('mail.session.batch.size', GROUP_SEND_BATCH_SIZE))
        for batch_email_member in tools.split_every(batch_size, member_emails.items()):
            mail_values = []
            for email_member_normalized, email_member in batch_email_member:
                if email_member_normalized == message.email_from_normalized:
                    # Do not send the email to their author
                    continue

                # SMTP headers related to the subscription
                email_url_encoded = urls.url_quote(email_member)
                unsubscribe_url = self._get_email_unsubscribe_url(email_member_normalized)

                headers = {
                    ** self._notify_by_email_get_headers(),
                    'List-Archive': f'<{base_url}/groups/{self.env["ir.http"]._slug(self)}>',
                    'List-Subscribe': f'<{base_url}/groups?email={email_url_encoded}>',
                    'List-Unsubscribe': f'<{unsubscribe_url}>',
                    'List-Unsubscribe-Post': 'List-Unsubscribe=One-Click',
                    'Precedence': 'list',
                    'X-Auto-Response-Suppress': 'OOF',  # avoid out-of-office replies from MS Exchange
                }
                if self.alias_email:
                    headers.update({
                        'List-Id': f'<{self.alias_email}>',
                        'List-Post': f'<mailto:{self.alias_email}>',
                        'X-Forge-To': f'"{self.name}" <{self.alias_email}>',
                    })

                if message.mail_message_id.parent_id:
                    headers['In-Reply-To'] = message.mail_message_id.parent_id.message_id

                # Add the footer (member specific) in the body
                template_values = {
                    'mailto': f'{self.alias_email}',
                    'group_url': f'{base_url}/groups/{self.env["ir.http"]._slug(self)}',
                    'unsub_label': f'{base_url}/groups?unsubscribe',
                    'unsub_url':  unsubscribe_url,
                }
                footer = self.env['ir.qweb']._render('mail_group.mail_group_footer', template_values, minimal_qcontext=True)
                member_body = append_content_to_html(body, footer, plaintext=False)

                mail_values.append({
                    'auto_delete': True,
                    'attachment_ids': message.attachment_ids.ids,
                    'body_html': member_body,
                    'email_from': message.email_from,
                    'email_to': email_member,
                    'headers': json.dumps(headers),
                    'mail_message_id': message.mail_message_id.id,
                    'message_id': message.mail_message_id.message_id,
                    'model': 'mail.group',
                    'reply_to': message.mail_message_id.reply_to,
                    'res_id': self.id,
                    'subject': message.subject,
                })

            if mail_values:
                self.env['mail.mail'].sudo().create(mail_values)