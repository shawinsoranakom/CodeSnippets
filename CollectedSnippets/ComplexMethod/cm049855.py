def _message_add_suggested_recipients(self, force_primary_email=False):
        """ Generic implementation for finding suggested recipient to mail on
        a recordset. """
        suggested = {
            record.id: {'email_to_lst': [], 'partners': self.env['res.partner']}
            for record in self
        }
        defaults = self._message_add_default_recipients()

        # add responsible
        user_field = self._fields.get('user_id')
        if user_field and user_field.type == 'many2one' and user_field.comodel_name == 'res.users':
            # SUPERUSER because of a read on res.users that would crash otherwise
            for record_su in self.sudo():
                suggested[record_su.id]['partners'] += record_su.user_id.partner_id

        # add customers
        for record_id, values in defaults.items():
            suggested[record_id]['partners'] |= values['partners']

        # add email
        for record in self:
            if force_primary_email:
                suggested[record.id]['email_to_lst'] += tools.mail.email_split_and_format_normalize(force_primary_email)
            else:
                suggested[record.id]['email_to_lst'] += defaults[record.id]['email_to_lst']

        return suggested