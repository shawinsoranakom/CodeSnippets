def _mark_done(self):
        """ This method will:
        1. mark the state as 'done'
        2. send the certification email with attached document if
        - The survey is a certification
        - It has a certification_mail_template_id set
        - The user succeeded the test
        3. Notify survey subtype subscribers of the newly completed input
        Will also run challenge Cron to give the certification badge if any."""
        self.write({
            'end_datetime': fields.Datetime.now(),
            'state': 'done',
        })

        Challenge_sudo = self.env['gamification.challenge'].sudo()
        badge_ids = []
        self._notify_new_participation_subscribers()
        for user_input in self:
            if user_input.survey_id.certification and user_input.scoring_success:
                if user_input.survey_id.certification_mail_template_id and not user_input.test_entry:
                    user_input.survey_id.certification_mail_template_id.send_mail(user_input.id, email_layout_xmlid="mail.mail_notification_light")
                if user_input.survey_id.certification_give_badge:
                    badge_ids.append(user_input.survey_id.certification_badge_id.id)

            # Update predefined_question_id to remove inactive questions
            user_input.predefined_question_ids -= user_input._get_inactive_conditional_questions()

        if badge_ids:
            challenges = Challenge_sudo.search([('reward_id', 'in', badge_ids)])
            if challenges:
                Challenge_sudo._cron_update(ids=challenges.ids, commit=False)