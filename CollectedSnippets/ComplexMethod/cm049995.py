def _multiple_choice_question_answer_result(self, user_input_lines, question_correct_suggested_answers):
        correct_user_input_lines = user_input_lines.filtered(lambda line: line.answer_is_correct and not line.skipped).mapped('suggested_answer_id')
        incorrect_user_input_lines = user_input_lines.filtered(lambda line: not line.answer_is_correct and not line.skipped)
        if question_correct_suggested_answers and correct_user_input_lines == question_correct_suggested_answers:
            return 'correct'
        elif correct_user_input_lines and correct_user_input_lines < question_correct_suggested_answers:
            return 'partial'
        elif not correct_user_input_lines and incorrect_user_input_lines:
            return 'incorrect'
        else:
            return 'skipped'