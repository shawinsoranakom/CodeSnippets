def fma(self, other, third, context=None):
        """Fused multiply-add.

        Returns self*other+third with no rounding of the intermediate
        product self*other.

        self and other are multiplied together, with no rounding of
        the result.  The third operand is then added to the result,
        and a single final rounding is performed.
        """

        other = _convert_other(other, raiseit=True)
        third = _convert_other(third, raiseit=True)

        # compute product; raise InvalidOperation if either operand is
        # a signaling NaN or if the product is zero times infinity.
        if self._is_special or other._is_special:
            if context is None:
                context = getcontext()
            if self._exp == 'N':
                return context._raise_error(InvalidOperation, 'sNaN', self)
            if other._exp == 'N':
                return context._raise_error(InvalidOperation, 'sNaN', other)
            if self._exp == 'n':
                product = self
            elif other._exp == 'n':
                product = other
            elif self._exp == 'F':
                if not other:
                    return context._raise_error(InvalidOperation,
                                                'INF * 0 in fma')
                product = _SignedInfinity[self._sign ^ other._sign]
            elif other._exp == 'F':
                if not self:
                    return context._raise_error(InvalidOperation,
                                                '0 * INF in fma')
                product = _SignedInfinity[self._sign ^ other._sign]
        else:
            product = _dec_from_triple(self._sign ^ other._sign,
                                       str(int(self._int) * int(other._int)),
                                       self._exp + other._exp)

        return product.__add__(third, context)