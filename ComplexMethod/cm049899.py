def _notify_get_recipients(self, message, msg_vals=False, **kwargs):
        """ Compute recipients to notify based on subtype and followers. This
        method returns data structured as expected for ``_notify_recipients``.

        :param record message: <mail.message> record being notified. May be
          void as 'msg_vals' superseeds it;
        :param dict msg_vals: values dict used to create the message, allows to
          skip message usage and spare some queries if given;

        Kwargs allow to pass various parameters that are used by sub notification
        methods. See those methods for more details about supported parameters.
        Specific kwargs used in this method:

          * ``notify_author``: allows to notify the author, which is False by
            default as we don't want people to receive their own content. It is
            used notably when impersonating partners or having automated
            notifications send by current user, targeting current user;
          * ``notify_author_mention``: allows to notify the author if in direct
            recipients i.e. in 'partner_ids';
          * ``notify_skip_followers``: skip followers fetch. Notification relies
            on message 'partner_ids' explicit recipients only;
          * ``skip_existing``: check existing notifications and skip them in order
            to avoid having several notifications / partner as it would make
            constraints crash. This is disabled by default to optimize speed;

        TDE/XDO TODO: flag rdata directly, for example r['notif'] = 'ocn_client'
        and r['needaction']=False and correctly override _notify_get_recipients

        :return: list of recipients information (see
          ``MailFollowers._get_recipient_data()`` for more details) formatted
          like [
          {
            'active': partner.active;
            'email_normalized': partner.email_normalized;
            'id': id of the res.partner being recipient to notify;
            'is_follower': follows the message related document;
            'name': partner name;
            'lang': partner lang;
            'groups': res.group IDs if linked to a user;
            'notif': notification type, one of 'inbox', 'email', 'sms' (SMS App),
                'whatsapp (WhatsAapp);
            'share': is partner a customer (partner.partner_share);
            'type': partner usage ('customer', 'portal', 'user');
            'uid': user ID (in case of multiple users, internal then first found
                by ID);)
            'ushare': are users shared (if users, all users are shared);
          }, {...}]
        :rtype: list[dict]
        """
        msg_vals = msg_vals or {}
        msg_sudo = message.sudo()

        # get values from msg_vals or from message if msg_vals doen't exists
        pids = msg_vals['partner_ids'] if 'partner_ids' in msg_vals else msg_sudo.partner_ids.ids
        if kwargs.get('notify_skip_followers'):
            # when skipping followers, message acts like user notification, which means
            # relying on required recipients (pids) only
            message_type = 'user_notification'
        else:
            message_type = msg_vals['message_type'] if 'message_type' in msg_vals else msg_sudo.message_type
        subtype_id = msg_vals['subtype_id'] if 'subtype_id' in msg_vals else msg_sudo.subtype_id.id

        # is it possible to have record but no subtype_id ?
        recipients_data = []
        # compute partner-based recipients data: followers, mentionned partner ids
        res = self.env['mail.followers']._get_recipient_data(self, message_type, subtype_id, pids)[self.id if self else 0]
        # include optional additional emails
        outgoing_email_to_lst = email_split_and_normalize(
            msg_vals['outgoing_email_to'] if 'outgoing_email_to' in msg_vals else msg_sudo.outgoing_email_to
        )
        if not res and not outgoing_email_to_lst:
            return recipients_data

        # notify author of its own messages, False by default
        skip_author_id = False
        notify_author = kwargs.get('notify_author') or self.env.context.get('mail_notify_author')
        if not notify_author:
            notify_author_mention = kwargs.get('notify_author_mention') or self.env.context.get('mail_notify_author_mention')
            author_id = msg_vals.get('author_id') or message.author_id.id
            skip_author_id = self._message_compute_real_author(author_id).id
            # allow mention of author if in direct recipients
            if notify_author_mention and skip_author_id in pids:
                skip_author_id = False

        # avoid double email notification if already emailed in original email
        emailed_normalized = [email for email in email_normalize_all(
            f"{msg_vals.get('incoming_email_to', msg_sudo.incoming_email_to) or ''}, "
            f"{msg_vals.get('incoming_email_cc', msg_sudo.incoming_email_cc) or ''}"
        )]

        for pid, pdata in res.items():
            if pid and pid == skip_author_id:
                continue
            if pdata['active'] is False:
                continue
            if pdata['email_normalized'] in emailed_normalized:
                continue
            recipients_data.append(pdata)

        # include emails only
        recipients_data += [
            {
                'active': True,
                'email_normalized': email,
                'id': False,
                'is_follower': False,
                'name': name or email,
                'lang': False,
                'groups': [],
                'notif': 'email',
                'share': True,
                'type': 'customer',
                'uid': False,
                'ushare': False,
            } for name, email in outgoing_email_to_lst
        ]

        # avoid double notification (on demand due to additional queries)
        if kwargs.pop('skip_existing', False):
            pids = [r['id'] for r in recipients_data if r['id']]
            if pids:
                existing_notifications = self.env['mail.notification'].sudo().search([
                    ('res_partner_id', 'in', pids),
                    ('mail_message_id', 'in', message.ids)
                ])
                recipients_data = [
                    r for r in recipients_data
                    if r['id'] not in existing_notifications.res_partner_id.ids
                ]

        return recipients_data