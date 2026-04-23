def _detect_write_to_catchall(self, msg_dict):
        """Return True if directly contacts catchall."""
        # Note: tweaked in stable to avoid doing two times same search due to bugfix
        # (see odoo/odoo#161782), to clean when reaching master
        if self.env.context.get("mail_catchall_aliases"):
            catchall_aliases = self.env.context["mail_catchall_aliases"]
        else:
            catchall_aliases = self.env['mail.alias.domain'].search([]).mapped('catchall_email')

        email_to_list = [email_normalize(e) or e for e in email_split(msg_dict['to'])]
        # check it does not directly contact catchall; either (legacy) strict aka
        # all TOs belong are catchall, either (optional) any catchall in all TOs
        if self.env.context.get("mail_catchall_write_any_to"):
            return catchall_aliases and any(email_to in catchall_aliases for email_to in email_to_list)
        return (
            catchall_aliases and email_to_list and
            all(email_to in catchall_aliases for email_to in email_to_list)
        )