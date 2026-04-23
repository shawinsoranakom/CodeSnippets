def _split_by_mail_configuration(self):
        """Group the <mail.mail> based on their "email_from", their "alias domain"
        and their "mail_server_id".

        The <mail.mail> will have the "same sending configuration" if they have the same
        mail server, alias domain and mail from. For performance purpose, we can use an SMTP
        session in batch and therefore we need to group them by the parameter that will
        influence the mail server used.

        The same "sending configuration" may repeat in order to limit batch size
        according to the `mail.session.batch.size` system parameter.

        Return iterators over
            mail_server_id, email_from, Records<mail.mail>.ids
        """
        mail_values = self.with_context(prefetch_fields=False).read(['id', 'email_from', 'mail_server_id', 'record_alias_domain_id'])
        all_mail_servers = self.env['ir.mail_server'].sudo().search([], order='sequence, id')

        # First group the <mail.mail> per mail_server_id, per alias_domain (if no server) and per email_from
        group_per_email_from = defaultdict(list)
        for mail, values in zip(self, mail_values):
            # protect against ill-formatted email_from when formataddr was used on an already formatted email
            emails_from = tools.mail.email_split_and_format_normalize(values['email_from'])
            email_from = emails_from[0] if emails_from else values['email_from']
            mail_server_id = values['mail_server_id'][0] if values['mail_server_id'] else False
            alias_domain_id = values['record_alias_domain_id'][0] if values['record_alias_domain_id'] else False
            key = (mail_server_id, alias_domain_id, email_from, mail._filter_mail_mail_servers(all_mail_servers))
            group_per_email_from[key].append(values['id'])

        group_per_smtp_from = defaultdict(list)
        for (mail_server_id, alias_domain_id, email_from, allowed_mail_servers), mail_ids in group_per_email_from.items():
            if not mail_server_id:
                mail_server = self.env['ir.mail_server']
                if alias_domain_id:
                    alias_domain = self.env['mail.alias.domain'].sudo().browse(alias_domain_id)
                    mail_server = mail_server.with_context(
                        domain_notifications_email=alias_domain.default_from_email,
                        domain_bounce_address=alias_domain.bounce_email,
                    )
                mail_server, smtp_from = mail_server._find_mail_server(email_from, allowed_mail_servers)
                mail_server_id = mail_server.id if mail_server else False
            else:
                smtp_from = email_from

            group_per_smtp_from[(mail_server_id, alias_domain_id, smtp_from)].extend(mail_ids)

        batch_size = int(self.env['ir.config_parameter'].sudo().get_param('mail.session.batch.size')) or 1000
        for (mail_server_id, alias_domain_id, smtp_from), record_ids in group_per_smtp_from.items():
            for batch_ids in tools.split_every(batch_size, record_ids):
                yield mail_server_id, alias_domain_id, smtp_from, batch_ids