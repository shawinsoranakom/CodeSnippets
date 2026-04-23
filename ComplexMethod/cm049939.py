def invite_by_email(self, emails):
        """
        Send channel invitation emails to a list of email addresses. Existing members'
        email addresses are ignored.

        :param emails: List of email addresses to invite.
        :type emails: list[str]

        """
        if not self.env.user._is_internal() or not self.has_access("read"):
            raise AccessError(self.env._("You don't have access to invite users to this channel."))
        if not self._allow_invite_by_email():
            raise UserError(
                self.env._("Inviting by email is not allowed for this channel type (%s).")
                % self.channel_type
            )
        eligible_emails = OrderedSet(norm for email in emails if email and (norm := email_normalize(email)))
        # Removing emails linked to members of this channel.
        member_domain = Domain("channel_id", "=", self.id) & Domain.OR(
            [
                [(field, "=ilike", email)]
                for email in eligible_emails
                for field in ("guest_id.email", "partner_id.email")
            ],
        )
        eligible_emails -= set(
            self.env["discuss.channel.member"]
            .search_fetch(member_domain, ["partner_id", "guest_id"])
            .mapped(lambda m: email_normalize(m.partner_id.email or m.guest_id.email))
        )
        mail_body = Markup("<p>%s</p>") % self.env._(
            "%(user_name)s has invited you to the %(strong_start)s%(channel_name)s%(strong_end)s channel."
        ) % {
            "user_name": self.env.user.name,
            "channel_name": self.name,
            "strong_start": Markup("<strong>"),
            "strong_end": Markup("</strong>"),
        }
        to_create = []
        for addr in eligible_emails:
            body = self.env["ir.qweb"]._render(
                "mail.discuss_channel_invitation_template",
                {
                    "base_url": self.env["ir.config_parameter"].get_base_url(),
                    "channel": self,
                    "email_token": hash_sign(self.env(su=True), "mail.invite_email", addr),
                    "mail_body": mail_body,
                    "user": self.env.user,
                },
                minimal_qcontext=True,
            )
            to_create.append(
                {
                    "body_html": body,
                    "email_from": self.env.user.partner_id.email_formatted,
                    "email_to": addr,
                    "message_type": "user_notification",
                    "model": "discuss.channel",
                    "res_id": self.id,
                    "subject": self.env._("%(author_name)s has invited you to a channel")
                    % {"author_name": self.env.user.name},
                },
            )
        if not to_create:
            return
        try:
            # sudo - mail.mail: internal users having read access to the channel can invite others.
            self.env["mail.mail"].sudo().create(to_create).send(raise_exception=True)
        except MailDeliveryException as mde:
            error_msg = self.env._(
                "There was an error when trying to deliver your Email, please check your configuration."
            )
            if len(mde.args) == 2 and isinstance(mde.args[1], ConnectionRefusedError):
                error_msg = self.env._(
                    "Could not contact the mail server, please check your outgoing email server configuration."
                )
            raise UserError(error_msg) from mde