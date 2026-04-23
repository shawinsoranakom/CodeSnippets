def _get_pages_and_questions_to_show(self):
        """Filter question_and_pages_ids to include only valid pages and questions.

        Pages are invalid if they have no description. Questions are invalid if
        they are conditional and all their triggers are invalid.
        Triggers are invalid if they:
          - Are a page (not a question)
          - Have the wrong question type (`simple_choice` and `multiple_choice` are supported)
          - Are misplaced (positioned after the conditional question)
          - They are themselves conditional and were found invalid
        """
        self.ensure_one()
        invalid_questions = self.env['survey.question']
        questions_and_valid_pages = self.question_and_page_ids.filtered(
            lambda question: not question.is_page or not is_html_empty(question.description))

        for question in questions_and_valid_pages.filtered('triggering_answer_ids').sorted():
            for trigger in question.triggering_question_ids:
                if (trigger not in invalid_questions
                        and not trigger.is_page
                        and trigger.question_type in ['simple_choice', 'multiple_choice']
                        and (trigger.sequence < question.sequence
                             or (trigger.sequence == question.sequence and trigger.id < question.id))):
                    break
            else:
                # No valid trigger found
                invalid_questions |= question
        return questions_and_valid_pages - invalid_questions