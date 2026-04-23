def from_float(cls, f):
        """Converts a float to a decimal number, exactly.

        Note that Decimal.from_float(0.1) is not the same as Decimal('0.1').
        Since 0.1 is not exactly representable in binary floating point, the
        value is stored as the nearest representable value which is
        0x1.999999999999ap-4.  The exact equivalent of the value in decimal
        is 0.1000000000000000055511151231257827021181583404541015625.

        >>> Decimal.from_float(0.1)
        Decimal('0.1000000000000000055511151231257827021181583404541015625')
        >>> Decimal.from_float(float('nan'))
        Decimal('NaN')
        >>> Decimal.from_float(float('inf'))
        Decimal('Infinity')
        >>> Decimal.from_float(-float('inf'))
        Decimal('-Infinity')
        >>> Decimal.from_float(-0.0)
        Decimal('-0')

        """
        if isinstance(f, int):                # handle integer inputs
            sign = 0 if f >= 0 else 1
            k = 0
            coeff = str(abs(f))
        elif isinstance(f, float):
            if _math.isinf(f) or _math.isnan(f):
                return cls(repr(f))
            if _math.copysign(1.0, f) == 1.0:
                sign = 0
            else:
                sign = 1
            n, d = abs(f).as_integer_ratio()
            k = d.bit_length() - 1
            coeff = str(n*5**k)
        else:
            raise TypeError("argument must be int or float.")

        result = _dec_from_triple(sign, coeff, -k)
        if cls is Decimal:
            return result
        else:
            return cls(result)