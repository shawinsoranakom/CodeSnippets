def _compute_answer_score(self):
        """ Get values for: answer_is_correct and associated answer_score.

        Calculates whether an answer_is_correct and its score based on 'answer_type' and
        corresponding question. Handles choice (answer_type == 'suggestion') questions
        separately from other question types. Each selected choice answer is handled as an
        individual answer.

        If score depends on the speed of the answer, it is adjusted as follows:
         - If the user answers in less than 2 seconds, they receive 100% of the possible points.
         - If user answers after that, they receive 50% of the possible points + the remaining
            50% scaled by the time limit and time taken to answer [i.e. a minimum of 50% of the
            possible points is given to all correct answers]

        Example of updated values:
            * {'answer_is_correct': False, 'answer_score': 0} (default)
            * {'answer_is_correct': True, 'answer_score': 2.0}
        """
        for line in self:
            answer_is_correct, answer_score = False, 0
            if line.answer_type:
                # record selected suggested choice answer_score (can be: pos, neg, or 0)
                if line.question_id.question_type in ['simple_choice', 'multiple_choice']:
                    if line.answer_type == 'suggestion' and line.suggested_answer_id:
                        answer_score = line.suggested_answer_id.answer_score
                        answer_is_correct = line.suggested_answer_id.is_correct
                # for all other scored question cases, record question answer_score (can be: pos or 0)
                elif line.question_id.question_type in ['date', 'datetime', 'numerical_box']:
                    answer = line[f'value_{line.answer_type}']
                    if line.answer_type == 'numerical_box':
                        answer = float(answer)
                    elif line.answer_type == 'date':
                        answer = fields.Date.from_string(answer)
                    elif line.answer_type == 'datetime':
                        answer = fields.Datetime.from_string(answer)
                    if answer and answer == line.question_id[f'answer_{line.answer_type}']:
                        answer_is_correct = True
                        answer_score = line.question_id.answer_score

            # Session speed rating
            if (
                answer_score > 0
                and line.user_input_id.survey_id.session_speed_rating
                and line.user_input_id.is_session_answer
                and line.question_id.is_time_limited
            ):
                max_score_delay = 2
                time_limit = line.question_id.time_limit
                now = fields.Datetime.now()
                seconds_to_answer = (now - line.user_input_id.survey_id.session_question_start_time).total_seconds()
                question_remaining_time = time_limit - seconds_to_answer
                # if answered within the max_score_delay => leave score as is
                if question_remaining_time < 0 or line.question_id != line.user_input_id.survey_id.session_question_id:
                    answer_score /= 2
                elif seconds_to_answer > max_score_delay:  # linear decrease in score after 2 sec
                    score_proportion = (time_limit - seconds_to_answer) / (time_limit - max_score_delay)
                    answer_score = (answer_score / 2) * (1 + score_proportion)

            line.answer_is_correct = answer_is_correct
            line.answer_score = answer_score