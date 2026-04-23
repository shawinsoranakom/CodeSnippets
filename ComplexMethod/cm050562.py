def action_invite(self):
        """ Process the wizard content and proceed with sending the related email(s),
            rendering any template patterns on the fly if needed. This method is used both
            to add members as 'joined' (when adding attendees) and as 'invited' (on invitation),
            depending on the value of enroll_mode. Archived members can be invited or enrolled.
            They will become 'invited', or another status if enrolled depending on their progress.
            Invited members can be reinvited, or enrolled depending on enroll_mode. """
        self.ensure_one()

        if not self.send_email:
            return
        if not self.env.user.email:
            raise UserError(_("Unable to post message, please configure the sender's email address."))
        if not self.partner_ids:
            raise UserError(_("Please select at least one recipient."))

        mail_values = []
        attendees_to_reinvite = self.env['slide.channel.partner'].search([
            ('member_status', '=', 'invited'),
            ('channel_id', '=', self.channel_id.id),
            ('partner_id', 'in', self.partner_ids.ids)
        ]) if not self.enroll_mode else self.env['slide.channel.partner']

        channel_partners = self.channel_id._action_add_members(
            self.partner_ids - attendees_to_reinvite.partner_id,
            member_status='joined' if self.enroll_mode else 'invited',
            raise_on_access=True
        )
        if not self.enroll_mode:
            (attendees_to_reinvite | channel_partners).last_invitation_date = fields.Datetime.now()

        for channel_partner in (attendees_to_reinvite | channel_partners):
            mail_values.append(self._prepare_mail_values(channel_partner))
        self.env['mail.mail'].sudo().create(mail_values)

        return {'type': 'ir.actions.act_window_close'}