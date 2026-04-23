def _find_or_create_from_emails(self, emails, ban_emails=None,
                                    filter_found=None, additional_values=None,
                                    no_create=False, sort_key=None, sort_reverse=True):
        """ Based on a list of emails, find or (optionally) create partners.
        If an email is not unique (e.g. multi-email input), only the first found
        valid email in input is considered. Filter and sort options allow to
        tweak the way we link emails to partners (e.g. share partners only, ...).

        Optional additional values allow to customize the created partner. Data
        are given per normalized email as it the creation criterion.

        When an email is invalid but not void, it is used for search or create.
        It allows updating it afterwards e.g. with notifications resend which
        allows fixing typos / wrong emails.

        :param list emails: list of emails that can be formatted;
        :param list ban_emails: optional list of banished emails e.g. because
          it may interfere with master data like aliases;
        :param callable filter_found: if given, filters found partners based on emails;
        :param dict additional_values: additional values per normalized or
          raw invalid email given to partner creation. Typically used to
          propagate a company_id and customer information from related record.
          If email cannot be normalized, raw value is used as dict key instead;
        :param sort_key: an optional sorting key for sorting partners before
          finding one with matching email normalized. When several partners
          have the same email, users might want to give a preference based
          on e.g. company, being a customer or not, ... Default ordering is
          to use 'id ASC', which means older partners first as they are considered
          as more relevant compared to default 'complete_name';
        :param bool sort_reverse: given to sorted (see 'reverse' argument of sort);
        :param bool no_create: skip the 'create' part of 'find or create'. Allows
          to use tool as 'find and sort' without adding new partners in db;

        :return: res.partner records in a list, following order of emails. Using
          a list allows to to keep Falsy values when no match;
        :rtype: list
        """
        additional_values = additional_values or {}
        partners, tocreate_vals_list = self.env['res.partner'], []
        name_emails = [tools.parse_contact_from_email(email) for email in emails]

        # find valid emails_normalized, filtering out false / void values, and search
        # for existing partners based on those emails
        emails_normalized = {email_normalized
                             for _name, email_normalized in name_emails
                             if email_normalized and email_normalized not in (ban_emails or [])}
        # find partners for invalid (but not void) emails, aka either invalid email
        # either no email and a name that will be used as email
        names = {
            name.strip()
            for name, email_normalized in name_emails
            if not email_normalized and name.strip() and name.strip() not in (ban_emails or [])
        }
        if emails_normalized or names:
            domains = []
            if emails_normalized:
                domains.append([('email_normalized', 'in', list(emails_normalized))])
            if names:
                domains.append([('email', 'in', list(names))])
            partners += self.search(Domain.OR(domains), order='id ASC')
            if filter_found:
                partners = partners.filtered(filter_found)

        if not no_create:
            # create partners for valid email without any existing partner. Keep
            # only first found occurrence of each normalized email, aka: ('Norbert',
            # 'norbert@gmail.com'), ('Norbert With Surname', 'norbert@gmail.com')'
            # -> a single partner is created for email 'norbert@gmail.com'
            seen = set()
            notfound_emails = emails_normalized - set(partners.mapped('email_normalized'))
            notfound_name_emails = [
                name_email
                for name_email in name_emails
                if name_email[1] in notfound_emails and name_email[1] not in seen
                and not seen.add(name_email[1])
            ]
            tocreate_vals_list += [
                {
                    self._rec_name: name or email_normalized,
                    'email': email_normalized,
                    **additional_values.get(email_normalized, {}),
                }
                for name, email_normalized in notfound_name_emails
                if email_normalized not in (ban_emails or [])
            ]
            # create partners for invalid emails (aka name and not email_normalized)
            # without any existing partner
            tocreate_vals_list += [
                {
                    self._rec_name: name,
                    'email': name,
                    **additional_values.get(name, {}),
                }
                for name in names if name not in partners.mapped('email') and name not in (ban_emails or [])
            ]
            # create partners once, avoid current user being followers of those
            if tocreate_vals_list:
                partners += self.with_context(mail_create_nosubscribe=True).create(tocreate_vals_list)

        # sort partners (already ordered based on search)
        if sort_key:
            partners = partners.sorted(key=sort_key, reverse=sort_reverse)

        return [
            next(
                (partner for partner in partners
                    if (email_normalized and partner.email_normalized == email_normalized)
                    or (not email_normalized and email and partner.email == email)
                    or (not email_normalized and name and partner.name == name)
                ),
                self.env['res.partner']
            )
            for (name, email_normalized), email in zip(name_emails, emails)
        ]