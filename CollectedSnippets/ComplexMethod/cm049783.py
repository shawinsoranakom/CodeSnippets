def _generate_notify_recipients(self, partners, record=None):
        """ Tool method to generate recipients data according to structure used
        in notification methods. Purpose is to allow testing of internals of
        some notification methods, notably testing links or group-based notification
        details.

        See notably ``MailThread._notify_get_recipients()``.
        """
        return [
            {'id': partner.id,
             'active': partner.active,
             'email_normalized': partner.email_normalized,
             'is_follower': partner in record.message_partner_ids if record else False,
             'groups': partner.user_ids.group_ids.ids,
             'lang': partner.lang,
             'name': partner.name,
             'notif': partner.user_ids.notification_type or 'email',
             'share': partner.partner_share,
             'type': 'user' if partner.main_user_id and partner.main_user_id._is_internal() else 'customer',
             'uid': partner.main_user_id.id,
             'ushare': all(user.share for user in partner.user_ids) if partner.user_ids else False,
            } for partner in partners
        ]