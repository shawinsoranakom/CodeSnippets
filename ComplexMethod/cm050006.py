def _get_stats_data_answers(self, user_input_lines):
        """ Statistics for question.answer based questions (simple choice, multiple
        choice.). A corner case with a void record survey.question.answer is added
        to count comments that should be considered as valid answers. This small hack
        allow to have everything available in the same standard structure. """
        suggested_answers = [answer for answer in self.mapped('suggested_answer_ids')]
        if self.comment_count_as_answer:
            suggested_answers += [self.env['survey.question.answer']]

        count_data = dict.fromkeys(suggested_answers, 0)
        for line in user_input_lines:
            if line.suggested_answer_id in count_data\
               or (line.value_char_box and self.comment_count_as_answer):
                count_data[line.suggested_answer_id] += 1

        table_data = [{
            'value': _('Other (see comments)') if not suggested_answer else suggested_answer.value_label,
            'suggested_answer': suggested_answer,
            'count': count_data[suggested_answer],
            'count_text': self.env._("%s Votes", count_data[suggested_answer]),
            }
            for suggested_answer in suggested_answers]
        graph_data = [{
            'text': self.env._('Other (see comments)') if not suggested_answer else suggested_answer.value_label,
            'count': count_data[suggested_answer]
            }
            for suggested_answer in suggested_answers]

        return table_data, graph_data