def write(self, vals):
        log_portal_access = 'group_ids' in vals and not self.env.context.get('mail_create_nolog') and not self.env.context.get('mail_notrack')
        user_portal_access_dict = {
            user.id: user._is_portal()
            for user in self
        } if log_portal_access else {}

        previous_email_by_user = {}
        if vals.get('email'):
            previous_email_by_user = {
                user: user.email
                for user in self.filtered(lambda user: bool(user.email_normalized))
                if user.email_normalized != email_normalize(vals['email'])
            }
        if 'notification_type' in vals:
            user_notification_type_modified = self.filtered(lambda user: user.notification_type != vals['notification_type'])

        write_res = super().write(vals)

        # log a portal status change (manual tracking)
        if log_portal_access:
            for user in self:
                user_has_group = user._is_portal()
                portal_access_changed = user_has_group != user_portal_access_dict[user.id]
                if portal_access_changed:
                    body = user._get_portal_access_update_body(user_has_group)
                    user.partner_id.message_post(
                        body=body,
                        message_type='notification',
                        subtype_xmlid='mail.mt_note'
                    )

        if 'login' in vals:
            self._notify_security_setting_update(
                _("Security Update: Login Changed"),
                _("Your account login has been updated"),
            )
        if 'password' in vals:
            self._notify_security_setting_update(
                _("Security Update: Password Changed"),
                _("Your account password has been updated"),
            )
        if 'email' in vals:
            # when the email is modified, we want notify the previous address (and not the new one)
            for user, previous_email in previous_email_by_user.items():
                self._notify_security_setting_update(
                    _("Security Update: Email Changed"),
                    _(
                        "Your account email has been changed from %(old_email)s to %(new_email)s.",
                        old_email=previous_email,
                        new_email=user.email,
                    ),
                    mail_values={'email_to': previous_email},
                    suggest_password_reset=False,
                )
        if "notification_type" in vals:
            for user in user_notification_type_modified:
                Store(bus_channel=user).add(user, "notification_type").bus_send()

        return write_res