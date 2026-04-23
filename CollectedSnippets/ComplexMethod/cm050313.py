def report_progress(self, users=(), subset_goals=False):
        """Post report about the progress of the goals

        :param users: users that are concerned by the report. If False, will
                      send the report to every user concerned (goal users and
                      group that receive a copy). Only used for challenge with
                      a visibility mode set to 'personal'.
        :param subset_goals: goals to restrict the report
        """

        challenge = self

        if challenge.visibility_mode == 'ranking':
            lines_boards = challenge._get_serialized_challenge_lines(restrict_goals=subset_goals)

            body_html = challenge.report_template_id.with_context(challenge_lines=lines_boards)._render_field('body_html', challenge.ids)[challenge.id]

            # send to every follower and participant of the challenge
            challenge.message_post(
                body=body_html,
                partner_ids=challenge.mapped('user_ids.partner_id.id'),
                subtype_xmlid='mail.mt_comment',
                email_layout_xmlid='mail.mail_notification_light',
                )
            if challenge.report_message_group_id:
                challenge.report_message_group_id.message_post(
                    body=body_html,
                    subtype_xmlid='mail.mt_comment')

        else:
            # generate individual reports
            for user in (users or challenge.user_ids):
                lines = challenge._get_serialized_challenge_lines(user, restrict_goals=subset_goals)
                if not lines:
                    continue
                # Avoid error if 'full_suffix' is missing in the line
                for line in lines:
                    line.setdefault('full_suffix', '')
                body_html = challenge.report_template_id.with_user(user).with_context(challenge_lines=lines)._render_field('body_html', challenge.ids)[challenge.id]

                # notify message only to users, do not post on the challenge
                challenge.message_notify(
                    body=body_html,
                    partner_ids=[user.partner_id.id],
                    subtype_xmlid='mail.mt_comment',
                    email_layout_xmlid='mail.mail_notification_light',
                )
                if challenge.report_message_group_id:
                    challenge.report_message_group_id.message_post(
                        body=body_html,
                        subtype_xmlid='mail.mt_comment',
                        email_layout_xmlid='mail.mail_notification_light',
                    )
        return challenge.write({'last_report_date': fields.Date.today()})