def _extract_header_types(self, preview_values, options):
        """ Returns the potential field types, based on the preview values, using heuristics.

        This methods is only used for suggested mapping at 2 levels:

        1. for fuzzy mapping at file load -> Execute the fuzzy mapping only
           on "most likely field types"
        2. For "Suggested fields" section in the fields mapping dropdown list at UI side.

        The following heuristic is used: If all preview values

        - Start with ``__export__``: return id + relational field types
        - Can be cast into integer: return id + relational field types, integer, float and monetary
        - Can be cast into Boolean: return boolean
        - Can be cast into float: return float, monetary
        - Can be cast into date/datetime: return date / datetime
        - Cannot be cast into any of the previous types: return only text based fields

        :param preview_values: list of value for the column to determine
                               see :meth:`parse_preview` for more details.
        :param options: parsing options
        """
        if all(isinstance(v, str) for v in preview_values):
            preview_values = [v.strip() for v in preview_values]
            values = set(preview_values)
            # If all values are empty in preview than can be any field
            if values == {''}:
                return ['all']

            # If all values starts with __export__ this is probably an id
            if all(v.startswith('__export__') for v in values):
                return ['id', 'many2many', 'many2one', 'one2many']

            # If all values can be cast to int type is either id, float or monetary
            # Exception: if we only have 1 and 0, it can also be a boolean
            if all(v.isdigit() for v in values if v):
                field_type = ['integer', 'float', 'monetary']
                if {'0', '1', ''}.issuperset(values):
                    field_type.append('boolean')
                return field_type

            # If all values are either True or False, type is boolean
            if all(val.lower() in ('true', 'false', 't', 'f', '') for val in preview_values):
                return ['boolean']

            # If all values can be cast to float, type is either float or monetary
            try:
                thousand_separator = decimal_separator = False
                for val in preview_values:
                    val = val.strip()
                    if not val:
                        continue
                    # value might have the currency symbol left or right from the value
                    val = self._remove_currency_symbol(val)
                    if val:
                        if options.get('float_thousand_separator') and options.get('float_decimal_separator'):
                            if options['float_decimal_separator'] == '.' and val.count('.') > 1:
                                # This is not a float so exit this try
                                float('a')
                            val = val.replace(options['float_thousand_separator'], '').replace(options['float_decimal_separator'], '.')
                        # We are now sure that this is a float, but we still need to find the
                        # thousand and decimal separator
                        else:
                            if val.count('.') > 1:
                                options['float_thousand_separator'] = '.'
                                options['float_decimal_separator'] = ','
                            elif val.count(',') > 1:
                                options['float_thousand_separator'] = ','
                                options['float_decimal_separator'] = '.'
                            elif val.find('.') > val.find(','):
                                thousand_separator = ','
                                decimal_separator = '.'
                            elif val.find(',') > val.find('.'):
                                thousand_separator = '.'
                                decimal_separator = ','
                    else:
                        # This is not a float so exit this try
                        float('a')
                if thousand_separator and not options.get('float_decimal_separator'):
                    options['float_thousand_separator'] = thousand_separator
                    options['float_decimal_separator'] = decimal_separator
                return ['float', 'monetary']  # Allow float to be mapped on a text field.
            except ValueError:
                pass

        results = self._try_match_date_time(preview_values, options)
        if results:
            return results

        # If not boolean, date/datetime, float or integer, only suggest text based fields.
        return ['text', 'char', 'binary', 'selection', 'html', 'tags']