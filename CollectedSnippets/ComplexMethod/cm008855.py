def _resolve_field_value(self, field, value, convert_none=False):
        if value is None:
            if not convert_none:
                return None
        else:
            value = value.lower()
        conversion = self._get_field_setting(field, 'convert')
        if conversion == 'ignore':
            return None
        if conversion == 'string':
            return value
        elif conversion == 'float_none':
            return float_or_none(value)
        elif conversion == 'bytes':
            return parse_bytes(value)
        elif conversion == 'order':
            order_list = (self._use_free_order and self._get_field_setting(field, 'order_free')) or self._get_field_setting(field, 'order')
            use_regex = self._get_field_setting(field, 'regex')
            list_length = len(order_list)
            empty_pos = order_list.index('') if '' in order_list else list_length + 1
            if use_regex and value is not None:
                for i, regex in enumerate(order_list):
                    if regex and re.match(regex, value):
                        return list_length - i
                return list_length - empty_pos  # not in list
            else:  # not regex or  value = None
                return list_length - (order_list.index(value) if value in order_list else empty_pos)
        else:
            if value.isnumeric():
                return float(value)
            else:
                self.settings[field]['convert'] = 'string'
                return value