def _get_stats_graph_data_matrix(self, user_input_lines):
        suggested_answers = self.mapped('suggested_answer_ids')
        matrix_rows = self.mapped('matrix_row_ids')

        count_data = dict.fromkeys(itertools.product(matrix_rows, suggested_answers), 0)
        for line in user_input_lines:
            if line.matrix_row_id and line.suggested_answer_id:
                count_data[(line.matrix_row_id, line.suggested_answer_id)] += 1

        table_data = [{
            'row': row,
            'columns': [{
                'suggested_answer': suggested_answer,
                'count': count_data[(row, suggested_answer)]
            } for suggested_answer in suggested_answers],
        } for row in matrix_rows]
        graph_data = [{
            'key': suggested_answer.value,
            'values': [{
                'text': row.value,
                'count': count_data[(row, suggested_answer)]
                }
                for row in matrix_rows
            ]
        } for suggested_answer in suggested_answers]

        return table_data, graph_data