def _compute_is_scored_question(self):
        """ Computes whether a question "is scored" or not. Handles following cases:
          - inconsistent Boolean=None edge case that breaks tests => False
          - survey is not scored => False
          - 'date'/'datetime'/'numerical_box' question types w/correct answer => True
            (implied without user having to activate, except for numerical whose correct value is 0.0)
          - 'simple_choice / multiple_choice': set to True if any of suggested answers are marked as correct
          - question_type isn't scoreable (note: choice questions scoring logic handled separately) => False
        """
        for question in self:
            if question.is_scored_question is None or question.scoring_type == 'no_scoring':
                question.is_scored_question = False
            elif question.question_type == 'date':
                question.is_scored_question = bool(question.answer_date)
            elif question.question_type == 'datetime':
                question.is_scored_question = bool(question.answer_datetime)
            elif question.question_type == 'numerical_box' and question.answer_numerical_box:
                question.is_scored_question = True
            elif question.question_type in ['simple_choice', 'multiple_choice']:
                question.is_scored_question = any(question.suggested_answer_ids.mapped('is_correct'))
            else:
                question.is_scored_question = False