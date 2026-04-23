def _prepare_question_results_values(self, survey, user_input_lines):
        """ Prepares usefull values to display during the host session:

        - question_statistics_graph
          The graph data to display the bar chart for questions of type 'choice'
        - input_lines_values
          The answer values to text/date/datetime questions
        - answers_validity
          An array containing the is_correct value for all question answers.
          We need this special variable because of Chartjs data structure.
          The library determines the parameters (color/label/...) by only passing the answer 'index'
          (and not the id or anything else we can identify).
          In other words, we need to know if the answer at index 2 is correct or not.
        - answer_count
          The number of answers to the current question.
        - selected_answers
          The current question selected answers.
        """

        question = survey.session_question_id
        if not question:
            return {}
        answers_validity = []
        if (any(answer.is_correct for answer in question.suggested_answer_ids)):
            answers_validity = [answer.is_correct for answer in question.suggested_answer_ids]
            if question.comment_count_as_answer:
                answers_validity.append(False)

        full_statistics = question._prepare_statistics(user_input_lines)[0]
        input_line_values = []
        if question.question_type in ['char_box', 'date', 'datetime']:
            input_line_values = [{
                'id': line.id,
                'value': line['value_%s' % question.question_type]
            } for line in full_statistics.get('table_data', request.env['survey.user_input.line'])[:100]]

        return {
            'is_html_empty': is_html_empty,
            'question_statistics_graph': full_statistics.get('graph_data'),
            'input_line_values': input_line_values,
            'answers_validity': json.dumps(answers_validity),
            'answer_count': survey.session_question_answer_count,
            'attendees_count': survey.session_answer_count,
            'selected_answers': user_input_lines.suggested_answer_id.ids,
        }