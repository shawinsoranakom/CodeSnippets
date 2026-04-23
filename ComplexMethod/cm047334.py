def value_to_html(self, value, options):
        min_precision = options.get('min_precision')
        if 'decimal_precision' in options:
            precision = self.env['decimal.precision'].precision_get(options['decimal_precision'])
        elif options.get('precision') is None:
            int_digits = int(math.log10(abs(value))) + 1 if value != 0 else 1
            max_dec_digits = max(15 - int_digits, 0)
            # We display maximum 6 decimal digits or the number of significant decimal digits if it's lower
            precision = min(6, max_dec_digits)
            min_precision = min_precision or 1
        else:
            precision = options['precision']

        fmt = f'%.{precision}f'
        if min_precision and min_precision < precision:
            _, dec_part = float_utils.float_split_str(value, precision)
            digits_count = len(dec_part.rstrip('0'))
            if digits_count < min_precision:
                fmt = f'%.{min_precision}f'
            elif digits_count < precision:
                fmt = f'%.{digits_count}f'

        value = float_utils.float_round(value, precision_digits=precision)
        return self.user_lang().format(fmt, value, grouping=True).replace(r'-', '-\N{ZERO WIDTH NO-BREAK SPACE}')