def create(self, vals_list):
        # First of all, extract values to ensure emails are really unique (and don't modify values in place)
        new_values = []
        all_emails = []
        for value in vals_list:
            email = tools.email_normalize(value.get('email'))
            if not email:
                raise UserError(_('Invalid email address “%s”', value['email']))
            if email in all_emails:
                continue
            all_emails.append(email)
            new_value = dict(value, email=email)
            new_values.append(new_value)

        """ To avoid crash during import due to unique email, return the existing records if any """
        to_create = []
        bl_entries = {}
        if new_values:
            sql = '''SELECT email, id FROM mail_blacklist WHERE email = ANY(%s)'''
            emails = [v['email'] for v in new_values]
            self.env.cr.execute(sql, (emails,))
            bl_entries = dict(self.env.cr.fetchall())
            to_create = [v for v in new_values if v['email'] not in bl_entries]

        # TODO DBE Fixme : reorder ids according to incoming ids.
        results = super().create(to_create)
        return self.env['mail.blacklist'].browse(bl_entries.values()) | results