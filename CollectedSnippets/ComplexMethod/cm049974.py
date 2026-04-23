def assertAnswerLines(self, page, answer, answer_data):
        """ Check answer lines.

          :param dict answer_data:
            key = question ID
            value = {'value': [user input]}
        """
        lines = answer.user_input_line_ids.filtered(lambda l: l.page_id == page)
        answer_count = sum(len(user_input['value']) for user_input in answer_data.values())
        self.assertEqual(len(lines), answer_count)
        for qid, user_input in answer_data.items():
            answer_lines = lines.filtered(lambda l: l.question_id.id == qid)
            question = answer_lines[0].question_id  # TDE note: might have several answers for a given question
            if question.question_type == 'multiple_choice':
                values = user_input['value']
                answer_fname = self._type_match[question.question_type][1]
                self.assertEqual(
                    Counter(getattr(line, answer_fname).id for line in answer_lines),
                    Counter(values))
            elif question.question_type == 'simple_choice':
                [value] = user_input['value']
                answer_fname = self._type_match[question.question_type][1]
                self.assertEqual(getattr(answer_lines, answer_fname).id, value)
            elif question.question_type == 'matrix':
                [value_col, value_row] = user_input['value']
                answer_fname_col = self._type_match[question.question_type][1][0]
                answer_fname_row = self._type_match[question.question_type][1][1]
                self.assertEqual(getattr(answer_lines, answer_fname_col).id, value_col)
                self.assertEqual(getattr(answer_lines, answer_fname_row).id, value_row)
            else:
                [value] = user_input['value']
                answer_fname = self._type_match[question.question_type][1]
                if question.question_type == 'numerical_box':
                    self.assertEqual(getattr(answer_lines, answer_fname), float(value))
                else:
                    self.assertEqual(getattr(answer_lines, answer_fname), value)