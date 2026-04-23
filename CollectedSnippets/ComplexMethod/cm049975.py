def _add_question(self, page, name, qtype, **kwargs):
        constr_mandatory = kwargs.pop('constr_mandatory', True)
        constr_error_msg = kwargs.pop('constr_error_msg', 'TestError')

        sequence = kwargs.pop('sequence', False)
        if not sequence:
            sequence = page.question_ids[-1].sequence + 1 if page.question_ids else page.sequence + 1

        base_qvalues = {
            'sequence': sequence,
            'title': name,
            'question_type': qtype,
            'constr_mandatory': constr_mandatory,
            'constr_error_msg': constr_error_msg,
        }
        if qtype in ('simple_choice', 'multiple_choice'):
            base_qvalues['suggested_answer_ids'] = [
                (0, 0, {
                    'value': label['value'],
                    'answer_score': label.get('answer_score', 0),
                    'is_correct': label.get('is_correct', False)
                }) for label in kwargs.pop('labels')
            ]
        elif qtype == 'matrix':
            base_qvalues['matrix_subtype'] = kwargs.pop('matrix_subtype', 'simple')
            base_qvalues['suggested_answer_ids'] = [
                (0, 0, {'value': label['value'], 'answer_score': label.get('answer_score', 0)})
                for label in kwargs.pop('labels')
            ]
            base_qvalues['matrix_row_ids'] = [
                (0, 0, {'value': label['value'], 'answer_score': label.get('answer_score', 0)})
                for label in kwargs.pop('labels_2')
            ]
        else:
            pass
        base_qvalues.update(kwargs)
        question = self.env['survey.question'].create(base_qvalues)
        return question