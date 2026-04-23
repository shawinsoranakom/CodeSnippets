def _notify_thread_by_sms(self, message, recipients_data, msg_vals=False,
                              sms_content=None, sms_numbers=None, sms_pid_to_number=None,
                              put_in_queue=False, **kwargs):
        """ Notification method: by SMS.

        :param record message: <mail.message> record being notified. May be
          void as 'msg_vals' superseeds it;
        :param list recipients_data: list of recipients data based on <res.partner>
          records formatted like a list of dicts containing information. See
          ``MailThread._notify_get_recipients()``;
        :param dict msg_vals: values dict used to create the message, allows to
          skip message usage and spare some queries if given;

        :param sms_content: plaintext version of body, mainly to avoid
          conversion glitches by splitting html and plain text content formatting
          (e.g.: links, styling.).
          If not given, `msg_vals`'s `body` is used and converted from html to plaintext;
        :param sms_numbers: additional numbers to notify in addition to partners
          and classic recipients;
        :param sms_pid_to_number: force a number to notify for a given partner ID
          instead of taking its mobile / phone number;
        :param put_in_queue: use cron to send queued SMS instead of sending them
          directly;
        """
        msg_vals = msg_vals or {}
        sms_pid_to_number = sms_pid_to_number if sms_pid_to_number is not None else {}
        sms_numbers = sms_numbers if sms_numbers is not None else []
        sms_create_vals = []
        sms_all = self.env['sms.sms'].sudo()

        # pre-compute SMS data
        body = sms_content or html2plaintext(msg_vals['body'] if 'body' in msg_vals else message.body)
        sms_base_vals = {
            'body': body,
            'mail_message_id': message.id,
            'state': 'outgoing',
        }

        # notify from computed recipients_data (followers, specific recipients)
        partners_data = [r for r in recipients_data if r['notif'] == 'sms']
        partner_ids = [r['id'] for r in partners_data]
        if partner_ids:
            for partner in self.env['res.partner'].sudo().browse(partner_ids):
                number = sms_pid_to_number.get(partner.id) or partner.phone
                sms_create_vals.append(dict(
                    sms_base_vals,
                    partner_id=partner.id,
                    number=partner._phone_format(number=number) or number,
                ))

        # notify from additional numbers
        if sms_numbers:
            tocreate_numbers = [
                self._phone_format(number=sms_number) or sms_number
                for sms_number in sms_numbers
            ]
            existing_partners_numbers = {vals_dict['number'] for vals_dict in sms_create_vals}
            sms_create_vals += [dict(
                sms_base_vals,
                partner_id=False,
                number=n,
                state='outgoing' if n else 'error',
                failure_type='' if n else 'sms_number_missing',
            ) for n in tocreate_numbers if n not in existing_partners_numbers]

        # create sms and notification
        if sms_create_vals:
            sms_all |= self.env['sms.sms'].sudo().create(sms_create_vals)

            notif_create_values = [{
                'author_id': message.author_id.id,
                'mail_message_id': message.id,
                'res_partner_id': sms.partner_id.id,
                'sms_number': sms.number,
                'notification_type': 'sms',
                'sms_id_int': sms.id,
                'sms_tracker_ids': [Command.create({'sms_uuid': sms.uuid})] if sms.state == 'outgoing' else False,
                'is_read': True,  # discard Inbox notification
                'notification_status': 'ready' if sms.state == 'outgoing' else 'exception',
                'failure_type': '' if sms.state == 'outgoing' else sms.failure_type,
            } for sms in sms_all]
            if notif_create_values:
                self.env['mail.notification'].sudo().create(notif_create_values)

        if sms_all and not put_in_queue:
            sms_all.filtered(lambda sms: sms.state == 'outgoing').send(raise_exception=False)

        return True