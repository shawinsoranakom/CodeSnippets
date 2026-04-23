def _compute_survey_statistic(self):
        default_vals = {
            'answer_count': 0, 'answer_done_count': 0, 'success_count': 0,
            'answer_score_avg': 0.0, 'success_ratio': 0.0
        }
        stat = dict((cid, dict(default_vals, answer_score_avg_total=0.0)) for cid in self.ids)
        UserInput = self.env['survey.user_input']
        base_domain = [('survey_id', 'in', self.ids)]

        read_group_res = UserInput._read_group(base_domain, ['survey_id', 'state', 'scoring_percentage', 'scoring_success'], ['__count'])
        for survey, state, scoring_percentage, scoring_success, count in read_group_res:
            stat[survey.id]['answer_count'] += count
            stat[survey.id]['answer_score_avg_total'] += scoring_percentage
            if state == 'done':
                stat[survey.id]['answer_done_count'] += count
            if scoring_success:
                stat[survey.id]['success_count'] += count

        for survey_stats in stat.values():
            avg_total = survey_stats.pop('answer_score_avg_total')
            survey_stats['answer_score_avg'] = avg_total / (survey_stats['answer_count'] or 1)
            survey_stats['success_ratio'] = (survey_stats['success_count'] / (survey_stats['answer_count'] or 1.0))*100

        for survey in self:
            survey.update(stat.get(survey._origin.id, default_vals))