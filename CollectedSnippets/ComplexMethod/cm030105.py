def __format__(self, specifier, context=None, _localeconv=None):
        """Format a Decimal instance according to the given specifier.

        The specifier should be a standard format specifier, with the
        form described in PEP 3101.  Formatting types 'e', 'E', 'f',
        'F', 'g', 'G', 'n' and '%' are supported.  If the formatting
        type is omitted it defaults to 'g' or 'G', depending on the
        value of context.capitals.
        """

        # Note: PEP 3101 says that if the type is not present then
        # there should be at least one digit after the decimal point.
        # We take the liberty of ignoring this requirement for
        # Decimal---it's presumably there to make sure that
        # format(float, '') behaves similarly to str(float).
        if context is None:
            context = getcontext()

        spec = _parse_format_specifier(specifier, _localeconv=_localeconv)

        # special values don't care about the type or precision
        if self._is_special:
            sign = _format_sign(self._sign, spec)
            body = str(self.copy_abs())
            if spec['type'] == '%':
                body += '%'
            return _format_align(sign, body, spec)

        # a type of None defaults to 'g' or 'G', depending on context
        if spec['type'] is None:
            spec['type'] = ['g', 'G'][context.capitals]

        # if type is '%', adjust exponent of self accordingly
        if spec['type'] == '%':
            self = _dec_from_triple(self._sign, self._int, self._exp+2)

        # round if necessary, taking rounding mode from the context
        rounding = context.rounding
        precision = spec['precision']
        if precision is not None:
            if spec['type'] in 'eE':
                self = self._round(precision+1, rounding)
            elif spec['type'] in 'fF%':
                self = self._rescale(-precision, rounding)
            elif spec['type'] in 'gG' and len(self._int) > precision:
                self = self._round(precision, rounding)
        # special case: zeros with a positive exponent can't be
        # represented in fixed point; rescale them to 0e0.
        if not self and self._exp > 0 and spec['type'] in 'fF%':
            self = self._rescale(0, rounding)
        if not self and spec['no_neg_0'] and self._sign:
            adjusted_sign = 0
        else:
            adjusted_sign = self._sign

        # figure out placement of the decimal point
        leftdigits = self._exp + len(self._int)
        if spec['type'] in 'eE':
            if not self and precision is not None:
                dotplace = 1 - precision
            else:
                dotplace = 1
        elif spec['type'] in 'fF%':
            dotplace = leftdigits
        elif spec['type'] in 'gG':
            if self._exp <= 0 and leftdigits > -6:
                dotplace = leftdigits
            else:
                dotplace = 1

        # find digits before and after decimal point, and get exponent
        if dotplace < 0:
            intpart = '0'
            fracpart = '0'*(-dotplace) + self._int
        elif dotplace > len(self._int):
            intpart = self._int + '0'*(dotplace-len(self._int))
            fracpart = ''
        else:
            intpart = self._int[:dotplace] or '0'
            fracpart = self._int[dotplace:]
        exp = leftdigits-dotplace

        # done with the decimal-specific stuff;  hand over the rest
        # of the formatting to the _format_number function
        return _format_number(adjusted_sign, intpart, fracpart, exp, spec)