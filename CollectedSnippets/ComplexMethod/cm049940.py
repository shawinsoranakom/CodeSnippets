def _notify_get_recipients(self, message, msg_vals=False, **kwargs):
        # Override recipients computation as channel is not a standard
        # mail.thread document. Indeed there are no followers on a channel.
        # Instead of followers it has members that should be notified.
        msg_vals = msg_vals or {}

        # notify only user input (comment, whatsapp messages or incoming / outgoing emails)
        message_type = msg_vals['message_type'] if 'message_type' in msg_vals else message.message_type
        if message_type not in ('comment', 'email', 'email_outgoing', 'whatsapp_message'):
            return []

        recipients_data = []
        author_id = msg_vals.get("author_id") or message.author_id.id
        pids = msg_vals['partner_ids'] or [] if 'partner_ids' in msg_vals else message.partner_ids.ids
        if pids:
            email_from = tools.email_normalize(msg_vals.get('email_from') or message.email_from)
            self.env['res.partner'].flush_model(['active', 'email', 'partner_share'])
            self.env['res.users'].flush_model(['notification_type', 'partner_id'])
            sql_query = SQL(
                """
                SELECT DISTINCT ON (partner.id) partner.id,
                       partner.email_normalized,
                       partner.lang,
                       partner.name,
                       partner.partner_share,
                       users.id as uid,
                       COALESCE(users.notification_type, 'email') as notif,
                       COALESCE(users.share, FALSE) as ushare
                  FROM res_partner partner
             LEFT JOIN res_users users on partner.id = users.partner_id
                 WHERE partner.active IS TRUE
                       AND partner.email != %(email)s
                       AND partner.id IN %(partner_ids)s AND partner.id != %(author_id)s
                """,
                email=email_from or "",
                partner_ids=tuple(pids),
                author_id=author_id or 0,
            )
            self.env.cr.execute(sql_query)
            for partner_id, email_normalized, lang, name, partner_share, uid, notif, ushare in self.env.cr.fetchall():
                # ocn_client: will add partners to recipient recipient_data. more ocn notifications. We neeed to filter them maybe
                recipients_data.append({
                    'active': True,
                    'email_normalized': email_normalized,
                    'id': partner_id,
                    'is_follower': False,
                    'groups': [],
                    'lang': lang,
                    'name': name,
                    'notif': notif,
                    'share': partner_share,
                    'type': 'user' if not partner_share and notif else 'customer',
                    'uid': uid,
                    'ushare': ushare,
                })

        domain = Domain.AND([
            [("channel_id", "=", self.id)],
            [("partner_id", "!=", author_id)],
            [("partner_id.active", "=", True)],
            [("mute_until_dt", "=", False)],
            [("partner_id.user_ids.manual_im_status", "!=", "busy")],
            Domain.OR([
                [("channel_id.channel_type", "!=", "channel")],
                Domain.AND([
                    [("channel_id.channel_type", "=", "channel")],
                    Domain.OR([
                        [("custom_notifications", "=", "all")],
                        Domain.AND([
                            [("custom_notifications", "=", False)],
                            [("partner_id.user_ids.res_users_settings_ids.channel_notifications", "=", "all")],
                        ]),
                        Domain.AND([
                            [("custom_notifications", "=", "mentions")],
                            [("partner_id", "in", pids)],
                        ]),
                        Domain.AND([
                            [("custom_notifications", "=", False)],
                            [("partner_id.user_ids.res_users_settings_ids.channel_notifications", "=", False)],
                            [("partner_id", "in", pids)],
                        ]),
                    ]),
                ]),
            ]),
        ])
        # sudo: discuss.channel.member - read to get the members of the channel and res.users.settings of the partners
        members = self.env["discuss.channel.member"].sudo().search(domain)
        for member in members:
            recipients_data.append({
                "active": True,
                "id": member.partner_id.id,
                "is_follower": False,
                "groups": [],
                "lang": member.partner_id.lang,
                "notif": "web_push",
                "share": member.partner_id.partner_share,
                "type": "customer",
                "uid": False,
                "ushare": False,
            })
        return recipients_data