def _check_challenge_reward(self, force=False):
        """Actions for the end of a challenge

        If a reward was selected, grant it to the correct users.
        Rewards granted at:
            - the end date for a challenge with no periodicity
            - the end of a period for challenge with periodicity
            - when a challenge is manually closed
        (if no end date, a running challenge is never rewarded)
        """
        commit = self.env.context.get('commit_gamification') and self.env.cr.commit

        for challenge in self:
            (start_date, end_date) = start_end_date_for_period(challenge.period, challenge.start_date, challenge.end_date)
            yesterday = date.today() - timedelta(days=1)

            rewarded_users = self.env['res.users']
            challenge_ended = force or end_date == fields.Date.to_string(yesterday)
            if challenge.reward_id and (challenge_ended or challenge.reward_realtime):
                # not using start_date as intemportal goals have a start date but no end_date
                reached_goals = self.env['gamification.goal']._read_group([
                    ('challenge_id', '=', challenge.id),
                    ('end_date', '=', end_date),
                    ('state', '=', 'reached')
                ], groupby=['user_id'], aggregates=['__count'])
                for user, count in reached_goals:
                    if count == len(challenge.line_ids):
                        # the user has succeeded every assigned goal
                        if challenge.reward_realtime:
                            badges = self.env['gamification.badge.user'].search_count([
                                ('challenge_id', '=', challenge.id),
                                ('badge_id', '=', challenge.reward_id.id),
                                ('user_id', '=', user.id),
                            ])
                            if badges > 0:
                                # has already recieved the badge for this challenge
                                continue
                        challenge._reward_user(user, challenge.reward_id)
                        rewarded_users |= user
                        if commit:
                            commit()

            if challenge_ended:
                # open chatter message
                message_body = _("The challenge %s is finished.", challenge.name)

                if rewarded_users:
                    message_body += Markup("<br/>") + _(
                        "Reward (badge %(badge_name)s) for every succeeding user was sent to %(users)s.",
                        badge_name=challenge.reward_id.name,
                        users=", ".join(rewarded_users.mapped('display_name'))
                    )
                else:
                    message_body += Markup("<br/>") + _("Nobody has succeeded to reach every goal, no badge is rewarded for this challenge.")

                # reward bests
                reward_message = Markup("<br/> %(rank)d. %(user_name)s - %(reward_name)s")
                if challenge.reward_first_id:
                    (first_user, second_user, third_user) = challenge._get_topN_users(MAX_VISIBILITY_RANKING)
                    if first_user:
                        challenge._reward_user(first_user, challenge.reward_first_id)
                        message_body += Markup("<br/>") + _("Special rewards were sent to the top competing users. The ranking for this challenge is:")
                        message_body += reward_message % {
                            'rank': 1,
                            'user_name': first_user.name,
                            'reward_name': challenge.reward_first_id.name,
                        }
                    else:
                        message_body += _("Nobody reached the required conditions to receive special badges.")

                    if second_user and challenge.reward_second_id:
                        challenge._reward_user(second_user, challenge.reward_second_id)
                        message_body += reward_message % {
                            'rank': 2,
                            'user_name': second_user.name,
                            'reward_name': challenge.reward_second_id.name,
                        }
                    if third_user and challenge.reward_third_id:
                        challenge._reward_user(third_user, challenge.reward_third_id)
                        message_body += reward_message % {
                            'rank': 3,
                            'user_name': third_user.name,
                            'reward_name': challenge.reward_third_id.name,
                        }

                challenge.message_post(
                    partner_ids=[user.partner_id.id for user in challenge.user_ids],
                    body=message_body)
                if commit:
                    commit()

        return True