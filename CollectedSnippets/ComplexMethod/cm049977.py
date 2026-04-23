def test_statistics_scale(self):
        """ Test statistics of scale question. """
        with MockRequest(self.env):
            found_user_input_lines, _ = self.SurveyController._extract_filters_data(self.survey, {})
        data = self.question_scale._prepare_statistics(found_user_input_lines)[0]
        self.assertEqual(data['table_data'],
                         [{'value': str(value),
                           'suggested_answer': self.env['survey.question.answer'],
                           'count': 1 if value in (5, 7) else 0,
                           'count_text': f"{1 if value in (5, 7) else 0} Votes"}
                          for value in range(11)])
        self.assertEqual(json.loads(data['graph_data']),
                         [{'key': self.question_scale.title,
                           'values': [{'text': str(value),
                                       'count': 1 if value in (5, 7) else 0}
                                      for value in range(11)]}])
        self.assertEqual(data['numerical_max'], 7)
        self.assertEqual(data['numerical_min'], 5)
        self.assertEqual(data['numerical_average'], 6)
        # Test that a skipped value is not interpreted as a 0 value
        self.scale_answer_line_2.write({
            'value_scale': False,
            'skipped': True,
            'answer_type': False,
        })
        data = self.question_scale._prepare_statistics(found_user_input_lines)[0]
        self.assertEqual(data['table_data'],
                         [{'value': str(value),
                           'suggested_answer': self.env['survey.question.answer'],
                           'count': 1 if value == 5 else 0,
                           'count_text': f"{1 if value == 5 else 0} Votes"}
                          for value in range(11)])
        self.assertEqual(data['numerical_max'], 5)
        self.assertEqual(data['numerical_min'], 5)
        self.assertEqual(data['numerical_average'], 5)