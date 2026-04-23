def _split_by_delayed_batch(self, mail_server):
        """To not flag personal email servers as spam, we throttle them at X emails / minutes."""
        if not mail_server or not mail_server.owner_user_id:
            return self

        MAX_SEND = mail_server._get_personal_mail_servers_limit()

        current_minute = datetime.datetime.now().replace(second=0, microsecond=0)
        server_limit_minute = (
            mail_server.owner_limit_time
            if mail_server.owner_limit_time
            else current_minute - timedelta(minutes=1)
        )

        if server_limit_minute < current_minute:
            # Server limit is old, we can send up to the limit
            server_limit_minute = current_minute
            mail_server.owner_limit_time = current_minute
            mail_server.owner_limit_count = 0

        elif server_limit_minute > current_minute:
            # Should not happen except if we manually write on the field
            mail_server.owner_limit_time = current_minute
            mail_server.owner_limit_count = 0
            _logger.error(
                "Mail: invalid owner_limit_time %s > %s for %s",
                server_limit_minute,
                current_minute,
                mail_server.name,
            )

        # Send the oldest mails in priority if the CRON is late
        to_send = self.browse()
        to_delay = self.browse()
        notifs = self.env['mail.notification'].sudo().search([
            ('notification_type', '=', 'email'),
            ('mail_mail_id', 'in', self.ids),
            ('notification_status', 'not in', ('sent', 'canceled'))
        ])
        for mail in self.sorted(lambda k: (k.create_date, k.id)):
            if mail_server.owner_limit_count >= MAX_SEND:
                to_delay |= mail
            elif mail_server.owner_limit_count + (len(mail.recipient_ids) or 1) > MAX_SEND:
                # Because we split for each recipient, if we want to
                # respect the limit we have to create new mails
                # (the first one keep the email_to and the email_cc
                # so it might send 2 emails instead of 1,
                # see `_prepare_outgoing_list`)
                to_keep = MAX_SEND - mail_server.owner_limit_count
                recipient_ids = mail.recipient_ids
                new_mail = mail.with_user(mail.create_uid).sudo().copy({
                    'headers': mail.headers,
                    'mail_message_id': mail.mail_message_id.id,
                    'recipient_ids': recipient_ids[:to_keep].ids,
                })
                mail.write({
                    'recipient_ids': recipient_ids[to_keep:],
                    'email_cc': False,
                    'email_to': False,
                })
                mail_server.owner_limit_count += to_keep or 1
                notifs.filtered(lambda n: n.mail_mail_id == mail and n.res_partner_id in recipient_ids[:to_keep]).mail_mail_id = new_mail
                to_send |= new_mail
                to_delay |= mail
            else:
                to_send |= mail
                mail_server.owner_limit_count += len(mail.recipient_ids) or 1

        # Delay if necessary
        if to_delay:
            owner_limit_count = mail_server.owner_limit_count
            for mail in to_delay:
                if owner_limit_count < MAX_SEND:
                    owner_limit_count += len(mail.recipient_ids) or 1
                else:
                    owner_limit_count = len(mail.recipient_ids) or 1
                    server_limit_minute += timedelta(minutes=1)

                mail.scheduled_date = server_limit_minute

            self.env.ref('mail.ir_cron_mail_scheduler_action')._trigger(
                min(to_delay.mapped('scheduled_date')) + timedelta(seconds=59))

        _logger.info(
            "Mail: personal server %s: %s emails about to be sent / %s emails delayed",
            mail_server.name, len(to_send), len(to_delay))
        return to_send