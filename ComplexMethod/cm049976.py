def _create_one_question_per_type_with_scoring(self):
        all_questions = self.env['survey.question']
        for (question_type, _dummy) in self.env['survey.question']._fields['question_type'].selection:
            kwargs = {}
            kwargs['question_type'] = question_type
            if question_type == 'numerical_box':
                kwargs['answer_score'] = 1
                kwargs['answer_numerical_box'] = 5
            elif question_type == 'date':
                kwargs['answer_score'] = 2
                kwargs['answer_date'] = datetime.date(2023, 10, 16)
            elif question_type == 'datetime':
                kwargs['answer_score'] = 3
                kwargs['answer_datetime'] = datetime.datetime(2023, 11, 17, 8, 0, 0)
            elif question_type == 'multiple_choice':
                kwargs['answer_score'] = 4
                kwargs['labels'] = [
                    {'value': 'MChoice0', 'is_correct': True},
                    {'value': 'MChoice1', 'is_correct': True},
                    {'value': 'MChoice2'}
                ]
            elif question_type == 'simple_choice':
                kwargs['answer_score'] = 5
                kwargs['labels'] = [
                    {'value': 'SChoice0', 'is_correct': True},
                    {'value': 'SChoice1'}
                ]
            elif question_type == 'matrix':
                kwargs['labels'] = [{'value': 'Column0'}, {'value': 'Column1'}]
                kwargs['labels_2'] = [{'value': 'Row0'}, {'value': 'Row1'}]
            all_questions |= self._add_question(self.page_0, 'Q0', question_type, **kwargs)

        return all_questions