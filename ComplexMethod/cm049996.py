def _notify_new_participation_subscribers(self):
        subtype_id = self.env.ref('survey.mt_survey_survey_user_input_completed', raise_if_not_found=False)
        if not self.ids or not subtype_id:
            return
        author_id = self.env.ref('base.partner_root').id if self.env.user.is_public else self.env.user.partner_id.id
        # Only post if there are any followers
        recipients_data = self.env['mail.followers']._get_recipient_data(self.survey_id, 'notification', subtype_id.id)
        followed_survey_ids = [survey_id for survey_id, followers in recipients_data.items() if followers]
        for user_input in self.filtered(lambda user_input_: user_input_.survey_id.id in followed_survey_ids):
            survey_title = user_input.survey_id.title
            if user_input.partner_id:
                body = _(
                    '%(participant)s just participated in "%(survey_title)s".',
                    participant=user_input.partner_id.display_name,
                    survey_title=survey_title,
                )
            else:
                body = _('Someone just participated in "%(survey_title)s".', survey_title=survey_title)

            user_input.message_post(author_id=author_id, body=body, subtype_xmlid='survey.mt_survey_user_input_completed')