def _prepare_leaderboard_values(self):
        """ The leaderboard is descending and takes the total of the attendee points minus the
        current question score.
        We need both the total and the current question points to be able to show the attendees
        leaderboard and shift their position based on the score they have on the current question.
        This prepares a structure containing all the necessary data for the animations done on
        the frontend side.
        The leaderboard is sorted based on attendees score *before* the current question.
        The frontend will shift positions around accordingly. """

        self.ensure_one()

        leaderboard = self.env['survey.user_input'].search_read([
            ('survey_id', '=', self.id),
            ('create_date', '>=', self.session_start_time)
        ], [
            'id',
            'nickname',
            'scoring_total',
        ], limit=15, order="scoring_total desc")

        if leaderboard and self.session_state == 'in_progress' and \
           any(answer.answer_score for answer in self.session_question_id.suggested_answer_ids):
            question_scores = {}
            input_lines = self.env['survey.user_input.line'].search_read(
                    [('user_input_id', 'in', [score['id'] for score in leaderboard]),
                        ('question_id', '=', self.session_question_id.id)],
                    ['user_input_id', 'answer_score'])
            for input_line in input_lines:
                question_scores[input_line['user_input_id'][0]] = \
                    question_scores.get(input_line['user_input_id'][0], 0) + input_line['answer_score']

            score_position = 0
            for leaderboard_item in leaderboard:
                question_score = question_scores.get(leaderboard_item['id'], 0)
                leaderboard_item.update({
                    'updated_score': leaderboard_item['scoring_total'],
                    'scoring_total': leaderboard_item['scoring_total'] - question_score,
                    'leaderboard_position': score_position,
                    'max_question_score': sum(
                        score for score in self.session_question_id.suggested_answer_ids.mapped('answer_score')
                        if score > 0
                    ) or 1,
                    'question_score': question_score
                })
                score_position += 1
            leaderboard = sorted(
                leaderboard,
                key=lambda score: score['scoring_total'],
                reverse=True)

        return leaderboard