def message_new(self, msg_dict, custom_values=None):
        # remove default author when going through the mail gateway. Indeed we
        # do not want to explicitly set user_id to False; however we do not
        # want the gateway user to be responsible if no other responsible is
        # found.
        create_context = dict(self.env.context or {})
        create_context['default_user_ids'] = False
        if custom_values is None:
            custom_values = {}
        # Auto create partner if not existent when the task is created from email
        if not msg_dict.get('author_id') and msg_dict.get('email_from'):
            author = self.env['mail.thread']._partner_find_from_emails_single([msg_dict['email_from']], no_create=False)
            msg_dict['author_id'] = author.id

        defaults = {
            'name': msg_dict.get('subject') or _("No Subject"),
            'allocated_hours': 0.0,
            'partner_id': msg_dict.get('author_id'),
            'email_cc': ", ".join(self._mail_cc_sanitized_raw_dict(msg_dict.get('cc')).values()) if custom_values.get('project_id') else ""

        }
        defaults.update(custom_values)

        # users having email address matched from emails recepients are filtered out and added as assignees to the task
        if msg_dict.get('to'):
            internal_users, partner_emails_without_users, unmatched_partner_emails = self._find_internal_users_from_address_mail(msg_dict.get('to'), defaults.get('project_id'))
            # set only internal users as assignees
            defaults['user_ids'] = defaults.get('user_ids', []) + internal_users
            if custom_values.get("project_id") and (partner_emails_without_users or unmatched_partner_emails):
                defaults["email_cc"] = defaults.get("email_cc", "") + ", " + ", ".join(partner_emails_without_users + unmatched_partner_emails)
        task = super(ProjectTask, self.with_context(create_context)).message_new(msg_dict, custom_values=defaults)
        partners = task._partner_find_from_emails_single(tools.email_split((msg_dict.get('to') or '') + ',' + (msg_dict.get('cc') or '')), no_create=True)
        if task.project_id:
            task.message_subscribe(partners.ids)
        return task