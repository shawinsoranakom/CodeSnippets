def _notify_thread_with_out_of_office(self, message, recipients_data, msg_vals=False, **kwargs):
        """ Out-of-office automated answer at posting time. """
        ooo_messages = self.env['mail.message']
        # limit OOO generation to incoming emails on valid threads
        if not self or self._transient:
            return ooo_messages
        message_type = msg_vals['message_type'] if 'message_type' in (msg_vals or {}) else message.message_type
        if message_type not in ('comment', 'email'):
            return ooo_messages

        # message author to notify is either a valid partner, either an email only
        # (e.g. mail gateway, portal with token)
        recipient = self._message_compute_real_author((msg_vals or {}).get('author_id') or message.author_id.id).sudo()
        email_to = ((msg_vals or {}).get('email_from') or message.email_from) if not recipient else False
        if not recipient and not email_to:
            return ooo_messages

        # extract internal users being notified to check their OOO status
        # done manually (not when computing recipients data) as it would be costly
        # and difficult with potential inheritance (calendar, ...)
        pids = msg_vals['partner_ids'] if 'partner_ids' in (msg_vals or {}) else message.partner_ids.ids
        internal_uids = [
            r['uid'] for r in recipients_data if (
                r['active'] and
                r['id'] and r['id'] in pids and
                r['id'] not in recipient.ids and  # don't OOO myself
                r['uid'] and not r['share']
            )
        ]
        additional_users_su = self._notify_thread_with_out_of_office_get_additional_users(
            message, recipients_data, recipient, msg_vals=msg_vals,
        )
        users_to_check = self.env['res.users'].sudo().browse(internal_uids) | additional_users_su
        ooo_users = self.env['res.users'].sudo()
        if users_to_check:
            users_to_check.fetch(['is_out_of_office', 'out_of_office_message'])
            ooo_users = users_to_check.filtered(lambda u: u.is_out_of_office and not is_html_empty(u.out_of_office_message))
        if not ooo_users:
            return ooo_messages

        # limit number of real author / recipient exchanges to 1 every 4 days
        sent_su = self.env['mail.message'].sudo().search([
            ('author_id', 'in', ooo_users.partner_id.ids),
            ('message_type', '=', 'out_of_office'),
            '|', ('partner_ids', 'in', recipient.ids), ('outgoing_email_to', '=', email_to),
            ('date', '>=', '-4d'),
        ])
        already_mailed = sent_su.author_id

        # finally send OOO messages
        original_subject = msg_vals['subject'] if 'subject' in (msg_vals or {}) else message.subject
        for user in ooo_users.filtered(lambda u: u.partner_id not in already_mailed):
            body = self.env['ir.qweb']._render(
                'mail.message_notification_out_of_office',
                {
                    # content
                    'out_of_office_message': user.out_of_office_message,
                    'replied_body': msg_vals['body'] if 'body' in (msg_vals or {}) else message.body,
                    'signature': user.signature,
                    # tools
                    'is_html_empty': is_html_empty,
                },
                minimal_qcontext=True,
                raise_if_not_found=False,
            )
            ooo_messages += self.message_post(
                author_id=user.partner_id.id,
                body=body,
                email_from=user.email_formatted,
                mail_headers={
                    'Auto-Submitted': 'auto-replied',
                    'X-Auto-Response-Suppress': 'All',  # avoid out-of-office (and other automated) replies from MS Exchange
                },
                message_type='out_of_office',  # do not use 'auto_comment', like acknowledgements, notably to ease finding them / avoid repetitions
                notify_author=True,  # as current user could be the one receiving the OOO message
                notify_skip_followers=True,
                outgoing_email_to=email_to,
                partner_ids=recipient.ids,
                subject=_('Auto: %(subject)s', subject=(original_subject or self.display_name)),
                subtype_id=self.env.ref('mail.mt_comment').id,  # TDE check: note ? but what about portal / internal ?
            )
        return ooo_messages