def _create_moderation_rule(self, status):
        """Create a moderation rule <mail.group.moderation> with the given status.

        Update existing moderation rule for the same email address if found,
        otherwise create a new rule.
        """
        if status not in ('ban', 'allow'):
            raise ValueError(_('Wrong status (%s)', status))

        for message in self:
            if not email_normalize(message.email_from):
                raise UserError(_('The email "%s" is not valid.', message.email_from))

        existing_moderation = self.env['mail.group.moderation'].search(
            Domain.OR([
                [
                    ('email', '=', email_normalize(message.email_from)),
                    ('mail_group_id', '=', message.mail_group_id.id)
                ] for message in self
            ])
        )
        existing_moderation.status = status

        # Add the value in a set to create only 1 moderation rule per (email_normalized, group)
        moderation_to_create = {
            (email_normalize(message.email_from), message.mail_group_id.id)
            for message in self
            if email_normalize(message.email_from) not in existing_moderation.mapped('email')
        }

        self.env['mail.group.moderation'].create([
            {
                'email': email,
                'mail_group_id': mail_group_id,
                'status': status,
            } for email, mail_group_id in moderation_to_create])