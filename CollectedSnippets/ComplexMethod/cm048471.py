def _merge_move_itemgetter(self, distinct_fields, excluded_fields=None):
        fields = set(distinct_fields or []) - set(excluded_fields or [])
        float_fields = {f_name for f_name in fields if self.env['stock.move']._fields[f_name].type == 'float'}
        base_getter = itemgetter(*fields - float_fields)

        if not float_fields:
            return base_getter

        float_precision = {f_name: (self.env['stock.move']._fields[f_name].get_digits(self.env) or (False, 2))[1] for f_name in float_fields}
        if 'price_unit' in float_fields:
            price_unit_prec = self.env['decimal.precision'].precision_get('Product Price')
            currency_precision = min(self.company_id.mapped('currency_id.decimal_places')) if self.company_id else False
            float_precision['price_unit'] = min(currency_precision, price_unit_prec) if currency_precision else price_unit_prec

        def _get_formatted_float_fields(move, f_name, precision):
            # Round and cast the value of move.f_name into a string so that rounding errors do not prevent the merge
            rounded_value = float_round(move[f_name], precision_digits=precision[f_name])
            return "{:.{precision}f}".format(rounded_value, precision=precision[f_name])

        return lambda move: base_getter(move) + tuple(_get_formatted_float_fields(move, f_name, float_precision) for f_name in float_fields)