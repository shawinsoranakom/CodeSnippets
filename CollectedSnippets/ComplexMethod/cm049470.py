def message_post(self, body='', subject=None, email_from=None, author_id=None, **kwargs):
        """ Custom posting process. This model does not inherit from ``mail.thread``
        but uses the mail gateway so few methods should be defined.

        This custom posting process works as follow

          * create a ``mail.message`` based on incoming email;
          * create linked ``mail.group.message`` that encapsulates message in a
            format used in mail groups;
          * apply moderation rules;

        :returns: newly-created mail.message
        """
        self.ensure_one()
        # First create the <mail.message>
        Mailthread = self.env['mail.thread']
        values = dict((key, val) for key, val in kwargs.items() if key in self.env['mail.message']._fields)
        author_id, email_from = Mailthread._message_compute_author(author_id, email_from)

        values.update({
            'author_id': author_id,
            # sanitize then make valid Markup, notably for '_process_attachments_for_post'
            'body': Markup(self._clean_email_body(body)),
            'email_from': email_from,
            'model': self._name,
            'partner_ids': [],
            'res_id': self.id,
            'subject': subject,
        })

        # Force the "reply-to" to make the mail group flow work
        values['reply_to'] = self.env['mail.message']._get_reply_to(values)

        # ensure message ID so that replies go to the right thread
        if not values.get('message_id'):
            values['message_id'] = generate_tracking_message_id('%s-mail.group' % self.id)

        values.update(Mailthread._process_attachments_for_post(
            kwargs.get('attachments') or [],
            kwargs.get('attachment_ids') or [],
            values
        ))

        mail_message = Mailthread._message_create([values])

        # Find the <mail.group.message> parent
        group_message_parent_id = False
        if mail_message.parent_id:
            group_message_parent = self.env['mail.group.message'].search(
                [('mail_message_id', '=', mail_message.parent_id.id)])
            group_message_parent_id = group_message_parent.id if group_message_parent else False

        moderation_status = 'pending_moderation' if self.moderation else 'accepted'

        # Create the group message associated
        group_message = self.env['mail.group.message'].create({
            'mail_group_id': self.id,
            'mail_message_id': mail_message.id,
            'moderation_status': moderation_status,
            'group_message_parent_id': group_message_parent_id,
        })

        # Check the moderation rule to determine if we should accept or reject the email
        email_normalized = email_normalize(email_from)
        moderation_rule = self.env['mail.group.moderation'].search([
            ('mail_group_id', '=', self.id),
            ('email', '=', email_normalized),
        ], limit=1)

        if not self.moderation:
            self._notify_members(group_message)

        elif moderation_rule and moderation_rule.status == 'allow':
            group_message.action_moderate_accept()

        elif moderation_rule and moderation_rule.status == 'ban':
            group_message.action_moderate_reject()

        elif self.moderation_notify:
            self.env['mail.mail'].sudo().create({
                'author_id': self.env.user.partner_id.id,
                'auto_delete': True,
                'body_html': group_message.mail_group_id.moderation_notify_msg,
                'email_from': self.env.user.company_id.catchall_formatted or self.env.user.company_id.email_formatted,
                'email_to': email_from,
                'subject': 'Re: %s' % (subject or ''),
                'state': 'outgoing'
            })

        return mail_message