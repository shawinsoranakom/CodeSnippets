def _action_channel_open_invite_wizard(self, mail_template, enroll_mode=False):
        """ Open the invitation wizard to invite and add attendees to the course(s) in self.

        :param mail_template: mail.template used in the invite wizard.
        :param enroll_mode: true if we want to enroll the attendees invited through the wizard.
            False otherwise, adding them as 'invited', e.g. when using "Invite" action."""
        course_name = self.name if len(self) == 1 else ''
        local_context = dict(
            self.env.context,
            default_channel_id=self.id if len(self) == 1 else False,
            default_email_layout_xmlid='website_slides.mail_notification_channel_invite',
            default_enroll_mode=enroll_mode,
            default_template_id=mail_template and mail_template.id or False,
            default_use_template=bool(mail_template),
        )
        if enroll_mode:
            name = _('Enroll Attendees to %(course_name)s', course_name=course_name or _('a course'))
        else:
            name = _('Invite Attendees to %(course_name)s', course_name=course_name or _('a course'))

        return {
            'type': 'ir.actions.act_window',
            'views': [[False, 'form']],
            'res_model': 'slide.channel.invite',
            'target': 'new',
            'context': local_context,
            'name': name,
        }