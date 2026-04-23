def _get_correct_answers(self):
        """ Return a dictionary linking the scorable question ids to their correct answers.
        The questions without correct answers are not considered.
        """
        correct_answers = {}

        # Simple and multiple choice
        choices_questions = self.filtered(lambda q: q.question_type in ['simple_choice', 'multiple_choice'])
        if choices_questions:
            suggested_answers_data = self.env['survey.question.answer'].search_read(
                [('question_id', 'in', choices_questions.ids), ('is_correct', '=', True)],
                ['question_id', 'id'],
                load='', # prevent computing display_names
            )
            for data in suggested_answers_data:
                if not data.get('id'):
                    continue
                correct_answers.setdefault(data['question_id'], []).append(data['id'])

        # Numerical box, date, datetime
        for question in self - choices_questions:
            if question.question_type not in ['numerical_box', 'date', 'datetime']:
                continue
            answer = question[f'answer_{question.question_type}']
            if question.question_type == 'date':
                answer = tools.format_date(self.env, answer)
            elif question.question_type == 'datetime':
                answer = tools.format_datetime(self.env, answer, tz='UTC', dt_format=False)
            correct_answers[question.id] = answer

        return correct_answers