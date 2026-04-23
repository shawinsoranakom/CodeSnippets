def _can_go_back(self, answer, page_or_question):
        """ Check if the user can go back to the previous question/page for the currently
        viewed question/page.
        Back button needs to be configured on survey and, depending on the layout:
        - In 'page_per_section', we can go back if we're not on the first page
        - In 'page_per_question', we can go back if:
          - It is not a session answer (doesn't make sense to go back in session context)
          - We are not on the first question
          - The survey does not have pages OR this is not the first page of the survey
            (pages are displayed in 'page_per_question' layout when they have a description, see PR#44271)
        """
        self.ensure_one()
        if self.questions_layout == "one_page" or not self.users_can_go_back:
            return False
        if answer.state != 'in_progress' or answer.is_session_answer:
            return False
        if self.page_ids and page_or_question == self.page_ids[0]:
            return False
        return self.questions_layout == 'page_per_section' or page_or_question != answer.predefined_question_ids[0]