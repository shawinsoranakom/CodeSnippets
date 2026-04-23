def get_qunit_regex(self, test_params):
        filters = _get_filters(test_params)
        positive = [f'({re.escape(f)}.*)' for sign, f in filters if sign == '+']
        negative = [f'({re.escape(f)}.*)' for sign, f in filters if sign == '-']
        filter = ''
        if filters:
            positive_re = '|'.join(positive) or '.*'
            negative_re = '|'.join(negative)
            negative_re = f'(?!{negative_re})' if negative_re else ''
            filter = f'^({negative_re})({positive_re})$'
        return filter