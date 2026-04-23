def _get_survey_questions(self, answer=None, page_id=None, question_id=None):
        """ Returns a tuple containing: the survey question and the passed question_id / page_id
        based on the question_layout and the fact that it's a session or not.

        Breakdown of use cases:
        - We are currently running a session
          We return the current session question and it's id
        - The layout is page_per_section
          We return the questions for that page and the passed page_id
        - The layout is page_per_question
          We return the question for the passed question_id and the question_id
        - The layout is one_page
          We return all the questions of the survey and None

        In addition, we cross the returned questions with the answer.predefined_question_ids,
        that allows to handle the randomization of questions. """
        if answer and answer.is_session_answer:
            return self.session_question_id, self.session_question_id.id
        if self.questions_layout == 'page_per_section':
            if not page_id:
                raise ValueError("Page id is needed for question layout 'page_per_section'")
            page_or_question_id = int(page_id)
            questions = self.env['survey.question'].sudo().search(
                Domain('survey_id', '=', self.id) & Domain('page_id', '=', page_or_question_id))
        elif self.questions_layout == 'page_per_question':
            if not question_id:
                raise ValueError("Question id is needed for question layout 'page_per_question'")
            page_or_question_id = int(question_id)
            questions = self.env['survey.question'].sudo().browse(page_or_question_id)
        else:
            page_or_question_id = None
            questions = self.question_ids

        # we need the intersection of the questions of this page AND the questions prepared for that user_input
        # (because randomized surveys do not use all the questions of every page)
        if answer:
            questions = questions & answer.predefined_question_ids
        return questions, page_or_question_id