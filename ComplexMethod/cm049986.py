def _is_last_page_or_question(self, user_input, page_or_question):
        """ Check if the given question or page is the last one, accounting for conditional questions.

        A question/page will be determined as the last one if any of the following is true:
          - The survey layout is "one_page",
          - There are no more questions/page after `page_or_question` in `user_input`,
          - All the following questions are conditional AND were not triggered by previous answers.
            Not accounting for the question/page own conditionals.
        """
        if self.questions_layout == "one_page":
            return True
        pages_or_questions = self._get_pages_or_questions(user_input)
        current_page_index = pages_or_questions.ids.index(page_or_question.id)
        next_page_or_question_candidates = pages_or_questions[current_page_index + 1:]
        if not next_page_or_question_candidates:
            return True
        inactive_questions = user_input._get_inactive_conditional_questions()
        if self.questions_layout == 'page_per_question':
            return not (
                any(next_question not in inactive_questions for next_question in next_page_or_question_candidates)
            )
        elif self.questions_layout == 'page_per_section':
            for section in next_page_or_question_candidates:
                if any(next_question not in inactive_questions for next_question in section.question_ids):
                    return False
        return True