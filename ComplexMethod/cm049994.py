def _prepare_statistics(self):
        """ Prepares survey.user_input's statistics to display various charts on the frontend.
        Returns a structure containing answers statistics "by section" and "totals" for every input in self.

        e.g returned structure:
        {
            survey.user_input(1,): {
                'by_section': {
                    'Uncategorized': {
                        'question_count': 2,
                        'correct': 2,
                        'partial': 0,
                        'incorrect': 0,
                        'skipped': 0,
                    },
                    'Mathematics': {
                        'question_count': 3,
                        'correct': 1,
                        'partial': 1,
                        'incorrect': 0,
                        'skipped': 1,
                    },
                    'Geography': {
                        'question_count': 4,
                        'correct': 2,
                        'partial': 0,
                        'incorrect': 2,
                        'skipped': 0,
                    }
                },
                'totals' [{
                    'text': 'Correct',
                    'count': 5,
                }, {
                    'text': 'Partially',
                    'count': 1,
                }, {
                    'text': 'Incorrect',
                    'count': 2,
                }, {
                    'text': 'Unanswered',
                    'count': 1,
                }]
            }
        }"""
        res = dict((user_input, {
            'by_section': {}
        }) for user_input in self)

        scored_questions = self.mapped('predefined_question_ids').filtered(lambda question: question.is_scored_question)

        for question in scored_questions:
            if question.question_type == 'simple_choice':
                question_incorrect_scored_answers = question.suggested_answer_ids.filtered(lambda answer: not answer.is_correct and answer.answer_score > 0)

            if question.question_type in ['simple_choice', 'multiple_choice']:
                question_correct_suggested_answers = question.suggested_answer_ids.filtered(lambda answer: answer.is_correct)

            question_section = question.page_id.title or _('Uncategorized')
            for user_input in self:
                user_input_lines = user_input.user_input_line_ids.filtered(lambda line:
                    line.question_id == question and (line.answer_type != 'char_box' or question.comment_count_as_answer))
                if question.question_type == 'simple_choice':
                    answer_result_key = self._simple_choice_question_answer_result(user_input_lines, question_correct_suggested_answers, question_incorrect_scored_answers)
                elif question.question_type == 'multiple_choice':
                    answer_result_key = self._multiple_choice_question_answer_result(user_input_lines, question_correct_suggested_answers)
                else:
                    answer_result_key = self._simple_question_answer_result(user_input_lines)

                if question_section not in res[user_input]['by_section']:
                    res[user_input]['by_section'][question_section] = {
                        'question_count': 0,
                        'correct': 0,
                        'partial': 0,
                        'incorrect': 0,
                        'skipped': 0,
                    }

                res[user_input]['by_section'][question_section]['question_count'] += 1
                res[user_input]['by_section'][question_section][answer_result_key] += 1

        for user_input in self:
            correct_count = 0
            partial_count = 0
            incorrect_count = 0
            skipped_count = 0

            for section_counts in res[user_input]['by_section'].values():
                correct_count += section_counts.get('correct', 0)
                partial_count += section_counts.get('partial', 0)
                incorrect_count += section_counts.get('incorrect', 0)
                skipped_count += section_counts.get('skipped', 0)

            res[user_input]['totals'] = [
                {'text': _("Correct"), 'count': correct_count},
                {'text': _("Partially"), 'count': partial_count},
                {'text': _("Incorrect"), 'count': incorrect_count},
                {'text': _("Unanswered"), 'count': skipped_count}
            ]

        return res