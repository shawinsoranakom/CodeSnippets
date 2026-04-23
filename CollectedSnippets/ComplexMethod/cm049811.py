def action_setup_outgoing_mail_server(self, server_type):
        """Configure the outgoing mail servers."""
        user = self.env.user
        if not user.has_external_mail_server:
            raise UserError(_('You are not allowed to create a personal mail server.'))

        if not user._is_internal():
            raise UserError(_('Only internal users can configure a personal mail server.'))

        existing_mail_server = self.env["ir.mail_server"].sudo() \
            .with_context(active_test=False).search([("owner_user_id", "=", user.id)])

        if server_type == 'default':
            # Use the default server
            if existing_mail_server:
                existing_mail_server.unlink()

            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "message": _("Switching back to the default server."),
                    "type": "warning",
                },
            }

        email = user.email
        if not email:
            raise UserError(_("Please set your email before connecting your mail server."))

        normalized_email = tools.email_normalize(email)
        if (
            not normalized_email
            or "@" not in normalized_email
            # Be sure it's well parsed by `ir.mail_server`
            or self.env["ir.mail_server"]._parse_from_filter(normalized_email)
            != [normalized_email]
        ):
            raise UserError(_("Wrong email address %s.", email))

        # Check that the user's email is not used by `mail.alias.domain` to avoid leaking the outgoing emails
        alias_domain = self.env["mail.alias.domain"].sudo().search([])
        cli_default_from = tools.config.get("email_from")
        match_from_filter = self.env["ir.mail_server"]._match_from_filter
        if (
            any(match_from_filter(e, normalized_email) for e in alias_domain.mapped("default_from_email"))
            or (cli_default_from and match_from_filter(cli_default_from, normalized_email))
        ):
            raise UserError(_("Your email address is used by an alias domain, and so you can not create a mail server for it."))

        if (
            server_type == user.outgoing_mail_server_type
            and user.outgoing_mail_server_id.from_filter == normalized_email
            and user.outgoing_mail_server_id.smtp_user == normalized_email
        ):
            # Re-connect the account
            return self._get_mail_server_setup_end_action(user.outgoing_mail_server_id)

        if existing_mail_server:
            existing_mail_server.unlink()

        values = {
            # Will be un-archived once logged in
            # Archived personal server will be deleted in GC CRON
            # to clean pending connection that didn't finish
            "active": False,
            "name": _("%s's outgoing email", user.name),
            "smtp_user": normalized_email,
            "smtp_pass": False,
            "from_filter": normalized_email,
            "smtp_port": 587,
            "smtp_encryption": "starttls",
            "owner_user_id": user.id,
            **self._get_mail_server_values(server_type),
        }
        smtp_server = self.env["ir.mail_server"].sudo().create(values)
        return self._get_mail_server_setup_end_action(smtp_server)