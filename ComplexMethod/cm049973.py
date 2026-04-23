def test_answer_display_name(self):
        """ The "display_name" field in a survey.user_input.line is a computed field that will
        display the answer label for any type of question.
        Let us test the various question types. """

        questions = self._create_one_question_per_type()
        user_input = self._add_answer(self.survey, self.survey_user.partner_id)

        for question in questions:
            if question.question_type == 'char_box':
                question_answer = self._add_answer_line(question, user_input, 'Char box answer')
                self.assertEqual(question_answer.display_name, 'Char box answer')
            elif question.question_type == 'text_box':
                question_answer = self._add_answer_line(question, user_input, 'Text box answer')
                self.assertEqual(question_answer.display_name, 'Text box answer')
            elif question.question_type == 'numerical_box':
                question_answer = self._add_answer_line(question, user_input, 7)
                self.assertEqual(question_answer.display_name, '7.0')
            elif question.question_type == 'date':
                question_answer = self._add_answer_line(question, user_input, fields.Datetime.now())
                self.assertEqual(question_answer.display_name, '2020-02-15')
            elif question.question_type == 'datetime':
                question_answer = self._add_answer_line(question, user_input, fields.Datetime.now())
                self.assertEqual(question_answer.display_name, '2020-02-15 19:00:00')
            elif question.question_type == 'simple_choice':
                question_answer = self._add_answer_line(question, user_input, question.suggested_answer_ids[0].id)
                self.assertEqual(question_answer.display_name, 'SChoice0')
            elif question.question_type == 'multiple_choice':
                question_answer_1 = self._add_answer_line(question, user_input, question.suggested_answer_ids[0].id)
                self.assertEqual(question_answer_1.display_name, 'MChoice0')
                question_answer_2 = self._add_answer_line(question, user_input, question.suggested_answer_ids[1].id)
                self.assertEqual(question_answer_2.display_name, 'MChoice1')
            elif question.question_type == 'matrix':
                question_answer_1 = self._add_answer_line(question, user_input,
                    question.suggested_answer_ids[0].id, **{'answer_value_row': question.matrix_row_ids[0].id})
                self.assertEqual(question_answer_1.display_name, 'Column0: Row0')
                question_answer_2 = self._add_answer_line(question, user_input,
                    question.suggested_answer_ids[0].id, **{'answer_value_row': question.matrix_row_ids[1].id})
                self.assertEqual(question_answer_2.display_name, 'Column0: Row1')
            elif question.question_type == 'scale':
                question_answer = self._add_answer_line(question, user_input, '3')
                self.assertEqual(question_answer.display_name, '3')