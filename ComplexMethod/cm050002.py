def validate_question(self, answer, comment=None):
        """ Validate question, depending on question type and parameters
        for simple choice, text, date and number, answer is simply the answer of the question.
        For other multiple choices questions, answer is a list of answers (the selected choices
        or a list of selected answers per question -for matrix type-):

        - Simple answer : ``answer = 'example'`` or ``2`` or ``question_answer_id`` or ``2019/10/10``
        - Multiple choice : ``answer = [question_answer_id1, question_answer_id2, question_answer_id3]``
        - Matrix: ``answer = { 'rowId1' : [colId1, colId2,...], 'rowId2' : [colId1, colId3, ...] }``

        :returns: A dict ``{question.id: error}``, or an empty dict if no validation error.
        :rtype: dict[int, str]
        """
        self.ensure_one()
        if isinstance(answer, str):
            answer = answer.strip()
        # Empty answer to mandatory question
        # because in choices question types, comment can count as answer
        if not answer and self.question_type not in ['simple_choice', 'multiple_choice']:
            if self.constr_mandatory and not self.survey_id.users_can_go_back:
                return {self.id: self.constr_error_msg or _('This question requires an answer.')}
        else:
            if self.question_type == 'char_box':
                return self._validate_char_box(answer)
            elif self.question_type == 'numerical_box':
                return self._validate_numerical_box(answer)
            elif self.question_type in ['date', 'datetime']:
                return self._validate_date(answer)
            elif self.question_type in ['simple_choice', 'multiple_choice']:
                return self._validate_choice(answer, comment)
            elif self.question_type == 'matrix':
                return self._validate_matrix(answer)
            elif self.question_type == 'scale':
                return self._validate_scale(answer)
        return {}