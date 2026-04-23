def action_send_guidelines(self, members=None):
        """ Send guidelines to given members. """
        self.ensure_one()

        if not self.env.is_admin() and not self.is_moderator:
            raise UserError(_('Only an administrator or a moderator can send guidelines to group members.'))

        if not self.moderation_guidelines_msg:
            raise UserError(_('The guidelines description is empty.'))

        if self.is_closed:
            raise UserError(_("You can not send guidelines for a closed group."))

        template = self.env.ref('mail_group.mail_template_guidelines', raise_if_not_found=False)
        if not template:
            raise UserError(_('Template "mail_group.mail_template_guidelines" was not found. No email has been sent. Please contact an administrator to fix this issue.'))

        banned_emails = self.env['mail.group.moderation'].sudo().search([
            ('status', '=', 'ban'),
            ('mail_group_id', '=', self.id),
        ]).mapped('email')

        if members is None:
            members = self.member_ids
        members = members.filtered(lambda member: member.email_normalized not in banned_emails)

        for member in members:
            company = member.partner_id.company_id or self.env.company
            template.send_mail(
                member.id,
                email_values={
                    'author_id': self.env.user.partner_id.id,
                    'email_from': company.email_formatted or company.catchall_formatted,
                    'reply_to': company.email_formatted or company.catchall_formatted,
                },
            )

        _logger.info('Send guidelines to %i members', len(members))