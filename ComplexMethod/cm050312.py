def _get_serialized_challenge_lines(self, user=(), restrict_goals=(), restrict_top=0):
        """Return a serialised version of the goals information if the user has not completed every goal

        :param user: user retrieving progress (False if no distinction,
                     only for ranking challenges)
        :param restrict_goals: compute only the results for this subset of
                               gamification.goal ids, if False retrieve every
                               goal of current running challenge
        :param int restrict_top: for challenge lines where visibility_mode is
                                 ``ranking``, retrieve only the best
                                 ``restrict_top`` results and itself, if 0
                                 retrieve all restrict_goal_ids has priority
                                 over restrict_top

        format list
        # if visibility_mode == 'ranking'
        {
            'name': <gamification.goal.description name>,
            'description': <gamification.goal.description description>,
            'condition': <reach condition {lower,higher}>,
            'computation_mode': <target computation {manually,count,sum,python}>,
            'monetary': <{True,False}>,
            'suffix': <value suffix>,
            'action': <{True,False}>,
            'display_mode': <{progress,boolean}>,
            'target': <challenge line target>,
            'own_goal_id': <gamification.goal id where user_id == uid>,
            'goals': [
                {
                    'id': <gamification.goal id>,
                    'rank': <user ranking>,
                    'user_id': <res.users id>,
                    'name': <res.users name>,
                    'state': <gamification.goal state {draft,inprogress,reached,failed,canceled}>,
                    'completeness': <percentage>,
                    'current': <current value>,
                }
            ]
        },
        # if visibility_mode == 'personal'
        {
            'id': <gamification.goal id>,
            'name': <gamification.goal.description name>,
            'description': <gamification.goal.description description>,
            'condition': <reach condition {lower,higher}>,
            'computation_mode': <target computation {manually,count,sum,python}>,
            'monetary': <{True,False}>,
            'suffix': <value suffix>,
            'action': <{True,False}>,
            'display_mode': <{progress,boolean}>,
            'target': <challenge line target>,
            'state': <gamification.goal state {draft,inprogress,reached,failed,canceled}>,
            'completeness': <percentage>,
            'current': <current value>,
        }
        """
        Goals = self.env['gamification.goal']
        (start_date, end_date) = start_end_date_for_period(self.period)

        res_lines = []
        for line in self.line_ids:
            line_data = {
                'name': line.definition_id.name,
                'description': line.definition_id.description,
                'condition': line.definition_id.condition,
                'computation_mode': line.definition_id.computation_mode,
                'monetary': line.definition_id.monetary,
                'suffix': line.definition_id.suffix,
                'action': True if line.definition_id.action_id else False,
                'display_mode': line.definition_id.display_mode,
                'target': line.target_goal,
            }
            domain = [
                ('line_id', '=', line.id),
                ('state', '!=', 'draft'),
            ]
            if restrict_goals:
                domain.append(('id', 'in', restrict_goals.ids))
            else:
                # if no subset goals, use the dates for restriction
                if start_date:
                    domain.append(('start_date', '=', start_date))
                if end_date:
                    domain.append(('end_date', '=', end_date))

            if self.visibility_mode == 'personal':
                if not user:
                    raise exceptions.UserError(_("Retrieving progress for personal challenge without user information"))

                domain.append(('user_id', '=', user.id))

                goal = Goals.search_fetch(domain, ['current', 'completeness', 'state'], limit=1)
                if not goal:
                    continue

                if goal.state != 'reached':
                    return []
                line_data.update({
                    fname: goal[fname]
                    for fname in ['id', 'current', 'completeness', 'state']
                })
                res_lines.append(line_data)
                continue

            line_data['own_goal_id'] = False,
            line_data['goals'] = []
            goals = Goals.search(domain, order='id')
            if not goals:
                continue
            goals = goals.sorted(key=lambda goal: (
                -goal.completeness, -goal.current if line.condition == 'higher' else goal.current
            ))

            for ranking, goal in enumerate(goals):
                if user and goal.user_id == user:
                    line_data['own_goal_id'] = goal.id
                elif restrict_top and ranking > restrict_top:
                    # not own goal and too low to be in top
                    continue

                line_data['goals'].append({
                    'id': goal.id,
                    'user_id': goal.user_id.id,
                    'name': goal.user_id.name,
                    'rank': ranking,
                    'current': goal.current,
                    'completeness': goal.completeness,
                    'state': goal.state,
                })
            if len(goals) < 3:
                # display at least the top 3 in the results
                missing = 3 - len(goals)
                for ranking, mock_goal in enumerate([{'id': False,
                                                      'user_id': False,
                                                      'name': '',
                                                      'current': 0,
                                                      'completeness': 0,
                                                      'state': False}] * missing,
                                                    start=len(goals)):
                    mock_goal['rank'] = ranking
                    line_data['goals'].append(mock_goal)

            res_lines.append(line_data)
        return res_lines