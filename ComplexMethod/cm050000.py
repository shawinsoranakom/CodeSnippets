def _get_answer_value(self):
        self.ensure_one()
        if self.answer_type == 'char_box':
            return self.value_char_box
        elif self.answer_type == 'text_box':
            return self.value_text_box
        elif self.answer_type == 'numerical_box':
            return self.value_numerical_box
        elif self.answer_type == 'scale':
            return self.value_scale
        elif self.answer_type == 'date':
            return self.value_date
        elif self.answer_type == 'datetime':
            return self.value_datetime
        elif self.answer_type == 'suggestion':
            return self.suggested_answer_id.value