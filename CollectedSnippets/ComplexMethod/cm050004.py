def _validate_choice(self, answer, comment):
        """ Validates choice-based questions.
        - Checks that mandatory questions have at least one answer.
        - For 'simple_choice', ensures that exactly one answer is provided.
        """
        answers = answer if isinstance(answer, list) else ([answer] if answer else [])

        valid_answers_count = len(answers)
        if comment and self.comment_count_as_answer:
            valid_answers_count += 1

        if valid_answers_count == 0 and self.constr_mandatory and not self.survey_id.users_can_go_back:
            return {self.id: self.constr_error_msg or _('This question requires an answer.')}

        if valid_answers_count > 1 and self.question_type == 'simple_choice':
            return {self.id: _('For this question, you can only select one answer.')}

        return {}