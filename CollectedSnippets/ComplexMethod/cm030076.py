def __str__(self, eng=False, context=None):
        """Return string representation of the number in scientific notation.

        Captures all of the information in the underlying representation.
        """

        sign = ['', '-'][self._sign]
        if self._is_special:
            if self._exp == 'F':
                return sign + 'Infinity'
            elif self._exp == 'n':
                return sign + 'NaN' + self._int
            else: # self._exp == 'N'
                return sign + 'sNaN' + self._int

        # number of digits of self._int to left of decimal point
        leftdigits = self._exp + len(self._int)

        # dotplace is number of digits of self._int to the left of the
        # decimal point in the mantissa of the output string (that is,
        # after adjusting the exponent)
        if self._exp <= 0 and leftdigits > -6:
            # no exponent required
            dotplace = leftdigits
        elif not eng:
            # usual scientific notation: 1 digit on left of the point
            dotplace = 1
        elif self._int == '0':
            # engineering notation, zero
            dotplace = (leftdigits + 1) % 3 - 1
        else:
            # engineering notation, nonzero
            dotplace = (leftdigits - 1) % 3 + 1

        if dotplace <= 0:
            intpart = '0'
            fracpart = '.' + '0'*(-dotplace) + self._int
        elif dotplace >= len(self._int):
            intpart = self._int+'0'*(dotplace-len(self._int))
            fracpart = ''
        else:
            intpart = self._int[:dotplace]
            fracpart = '.' + self._int[dotplace:]
        if leftdigits == dotplace:
            exp = ''
        else:
            if context is None:
                context = getcontext()
            exp = ['e', 'E'][context.capitals] + "%+d" % (leftdigits-dotplace)

        return sign + intpart + fracpart + exp