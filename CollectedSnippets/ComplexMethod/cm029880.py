def __pow__(a, b, modulo=None):
        """a ** b

        If b is not an integer, the result will be a float or complex
        since roots are generally irrational. If b is an integer, the
        result will be rational.

        """
        if modulo is not None:
            return NotImplemented
        if isinstance(b, numbers.Rational):
            if b.denominator == 1:
                power = b.numerator
                if power >= 0:
                    return Fraction._from_coprime_ints(a._numerator ** power,
                                                       a._denominator ** power)
                elif a._numerator > 0:
                    return Fraction._from_coprime_ints(a._denominator ** -power,
                                                       a._numerator ** -power)
                elif a._numerator == 0:
                    raise ZeroDivisionError('Fraction(%s, 0)' %
                                            a._denominator ** -power)
                else:
                    return Fraction._from_coprime_ints((-a._denominator) ** -power,
                                                       (-a._numerator) ** -power)
            else:
                # A fractional power will generally produce an
                # irrational number.
                return float(a) ** float(b)
        elif isinstance(b, (float, complex)):
            return float(a) ** b
        else:
            return NotImplemented