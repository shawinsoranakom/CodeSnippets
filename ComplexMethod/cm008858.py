def _calculate_field_preference_from_value(self, format_, field, type_, value):
        reverse = self._get_field_setting(field, 'reverse')
        closest = self._get_field_setting(field, 'closest')
        limit = self._get_field_setting(field, 'limit')

        if type_ == 'extractor':
            maximum = self._get_field_setting(field, 'max')
            if value is None or (maximum is not None and value >= maximum):
                value = -1
        elif type_ == 'boolean':
            in_list = self._get_field_setting(field, 'in_list')
            not_in_list = self._get_field_setting(field, 'not_in_list')
            value = 0 if ((in_list is None or value in in_list) and (not_in_list is None or value not in not_in_list)) else -1
        elif type_ == 'ordered':
            value = self._resolve_field_value(field, value, True)

        # try to convert to number
        val_num = float_or_none(value, default=self._get_field_setting(field, 'default'))
        is_num = self._get_field_setting(field, 'convert') != 'string' and val_num is not None
        if is_num:
            value = val_num

        return ((-10, 0) if value is None
                else (1, value, 0) if not is_num  # if a field has mixed strings and numbers, strings are sorted higher
                else (0, -abs(value - limit), value - limit if reverse else limit - value) if closest
                else (0, value, 0) if not reverse and (limit is None or value <= limit)
                else (0, -value, 0) if limit is None or (reverse and value == limit) or value > limit
                else (-1, value, 0))