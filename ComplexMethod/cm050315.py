def _get_topN_users(self, n):
        """Get the top N users for a defined challenge

        Ranking criterias:
            1. succeed every goal of the challenge
            2. total completeness of each goal (can be over 100)

        Only users having reached every goal of the challenge will be returned
        unless the challenge ``reward_failure`` is set, in which case any user
        may be considered.

        :returns: an iterable of exactly N records, either User objects or
                  False if there was no user for the rank. There can be no
                  False between two users (if users[k] = False then
                  users[k+1] = False
        """
        Goals = self.env['gamification.goal']
        (start_date, end_date) = start_end_date_for_period(self.period, self.start_date, self.end_date)
        challengers = []
        for user in self.user_ids:
            all_reached = True
            total_completeness = 0
            # every goal of the user for the running period
            goal_ids = Goals.search([
                ('challenge_id', '=', self.id),
                ('user_id', '=', user.id),
                ('start_date', '=', start_date),
                ('end_date', '=', end_date)
            ])
            for goal in goal_ids:
                if goal.state != 'reached':
                    all_reached = False
                if goal.definition_condition == 'higher':
                    # can be over 100
                    total_completeness += (100.0 * goal.current / goal.target_goal) if goal.target_goal else 0
                elif goal.state == 'reached':
                    # for lower goals, can not get percentage so 0 or 100
                    total_completeness += 100

            challengers.append({'user': user, 'all_reached': all_reached, 'total_completeness': total_completeness})

        challengers.sort(key=lambda k: (k['all_reached'], k['total_completeness']), reverse=True)
        if not self.reward_failure:
            # only keep the fully successful challengers at the front, could
            # probably use filter since the successful ones are at the front
            challengers = itertools.takewhile(lambda c: c['all_reached'], challengers)

        # append a tail of False, then keep the first N
        challengers = itertools.islice(
            itertools.chain(
                (c['user'] for c in challengers),
                itertools.repeat(False),
            ), 0, n
        )

        return tuple(challengers)