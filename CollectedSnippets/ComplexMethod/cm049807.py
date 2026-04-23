def _find_aliases(self, email_list):
        """ Utility method to find both alias domains aliases (bounce, catchall
        or default from) and mail aliases from an email list.

        :param email_list: list of normalized emails; normalization / removing
            wrong emails is considered as being caller's job
        """
        filtered_emails = [e for e in email_list if e and '@' in e]
        if not filtered_emails:
            return filtered_emails
        all_domains = self.search([])
        aliases = set(all_domains.mapped('bounce_email') +
                    all_domains.mapped('catchall_email') +
                    all_domains.mapped('default_from_email'))

        # Get allowed domains and convert to a set for O(1) lookup
        catchall_params = self.env["ir.config_parameter"].sudo().get_param("mail.catchall.domain.allowed") or ''
        catchall_domains_allowed = set(filter(None, catchall_params.split(',')))
        if catchall_domains_allowed:
            catchall_domains_allowed.update(all_domains.mapped('name'))
            email_localparts_tocheck = [
                email.partition('@')[0] for email in filtered_emails if (
                    email.partition('@')[2] in catchall_domains_allowed
                )]
        else:
            email_localparts_tocheck = [email.partition('@')[0] for email in filtered_emails if email]

        # search on aliases using the proposed list, as we could have a lot of aliases
        # better than returning 'all alias emails'
        potential_aliases = self.env['mail.alias'].search([
            '|',
            ('alias_full_name', 'in', filtered_emails),
            '&', ('alias_name', 'in', email_localparts_tocheck), ('alias_incoming_local', '=', True),
        ])
        # Global aliases match by full name
        aliases.update(potential_aliases.filtered(lambda x: not x.alias_incoming_local).mapped('alias_full_name'))

        # Local aliases for validated local part + domain checking
        local_alias_names = set(potential_aliases.filtered(lambda x: x.alias_incoming_local).mapped('alias_name'))

        res = []
        for email in filtered_emails:
            if email in aliases:
                res.append(email)
                continue

            local_part, _, domain = email.partition('@')
            if local_part in local_alias_names and (not catchall_domains_allowed or domain in catchall_domains_allowed):
                res.append(email)

        return res