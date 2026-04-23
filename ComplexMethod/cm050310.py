def _update_all(self):
        """Update the challenges and related goals."""
        if not self:
            return True

        Goals = self.env['gamification.goal']
        self.flush_recordset()
        self.user_ids.presence_ids.flush_recordset()
        # include yesterday goals to update the goals that just ended
        # exclude goals for users that have not interacted with the
        # webclient since the last update or whose session is no longer
        # valid.
        yesterday = fields.Date.to_string(date.today() - timedelta(days=1))
        self.env.cr.execute("""SELECT gg.id
                        FROM gamification_goal as gg
                        JOIN mail_presence as mp ON mp.user_id = gg.user_id
                       WHERE gg.write_date <= mp.last_presence
                         AND mp.last_presence >= now() AT TIME ZONE 'UTC' - interval '%(session_lifetime)s seconds'
                         AND gg.closed IS NOT TRUE
                         AND gg.challenge_id IN %(challenge_ids)s
                         AND (gg.state = 'inprogress'
                              OR (gg.state = 'reached' AND gg.end_date >= %(yesterday)s))
                      GROUP BY gg.id
        """, {
            'session_lifetime': SESSION_LIFETIME,
            'challenge_ids': tuple(self.ids),
            'yesterday': yesterday
        })

        Goals.browse(goal_id for [goal_id] in self.env.cr.fetchall()).update_goal()

        self._recompute_challenge_users()
        self._generate_goals_from_challenge()

        for challenge in self:
            if challenge.last_report_date != fields.Date.today():
                if challenge.next_report_date and fields.Date.today() >= challenge.next_report_date:
                    challenge.report_progress()
                else:
                    # goals closed but still opened at the last report date
                    closed_goals_to_report = Goals.search([
                        ('challenge_id', '=', challenge.id),
                        ('start_date', '>=', challenge.last_report_date),
                        ('end_date', '<=', challenge.last_report_date)
                    ])
                    if closed_goals_to_report:
                        # some goals need a final report
                        challenge.report_progress(subset_goals=closed_goals_to_report)

        self._check_challenge_reward()
        return True