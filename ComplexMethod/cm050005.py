def _prepare_statistics(self, user_input_lines):
        """ Compute statistical data for questions by counting number of vote per choice on basis of filter """
        all_questions_data = []
        for question in self:
            question_data = {'question': question, 'is_page': question.is_page}

            if question.is_page:
                all_questions_data.append(question_data)
                continue

            # fetch answer lines, separate comments from real answers
            all_lines = user_input_lines.filtered(lambda line: line.question_id == question)
            if question.question_type in ['simple_choice', 'multiple_choice', 'matrix']:
                answer_lines = all_lines.filtered(
                    lambda line: line.answer_type == 'suggestion' or (
                        line.skipped and not line.answer_type) or (
                        line.answer_type == 'char_box' and question.comment_count_as_answer)
                    )
                comment_line_ids = all_lines.filtered(lambda line: line.answer_type == 'char_box')
            else:
                answer_lines = all_lines
                comment_line_ids = self.env['survey.user_input.line']
            skipped_lines = answer_lines.filtered(lambda line: line.skipped)
            done_lines = answer_lines - skipped_lines
            question_data.update(
                answer_line_ids=answer_lines,
                answer_line_done_ids=done_lines,
                answer_input_done_ids=done_lines.mapped('user_input_id'),
                answer_input_ids=answer_lines.mapped('user_input_id'),
                comment_line_ids=comment_line_ids)
            question_data.update(question._get_stats_summary_data(answer_lines))

            # prepare table and graph data
            table_data, graph_data = question._get_stats_data(answer_lines)
            question_data['table_data'] = table_data
            question_data['graph_data'] = json.dumps(graph_data)
            if question.question_type in ["text_box", "char_box", "numerical_box", "date", "datetime"]:
                answers_data = [
                    [input_line.id, input_line._get_answer_value(), input_line.user_input_id.get_print_url()]
                    for input_line in table_data if not input_line.skipped
                ]
                question_data["answers_data"] = json.dumps(answers_data, default=str)
            all_questions_data.append(question_data)
        return all_questions_data