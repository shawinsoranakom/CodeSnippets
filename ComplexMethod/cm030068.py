def _format_number(is_negative, intpart, fracpart, exp, spec):
    """Format a number, given the following data:

    is_negative: true if the number is negative, else false
    intpart: string of digits that must appear before the decimal point
    fracpart: string of digits that must come after the point
    exp: exponent, as an integer
    spec: dictionary resulting from parsing the format specifier

    This function uses the information in spec to:
      insert separators (decimal separator and thousands separators)
      format the sign
      format the exponent
      add trailing '%' for the '%' type
      zero-pad if necessary
      fill and align if necessary
    """

    sign = _format_sign(is_negative, spec)

    frac_sep = spec['frac_separators']
    if fracpart and frac_sep:
        fracpart = frac_sep.join(fracpart[pos:pos + 3]
                                 for pos in range(0, len(fracpart), 3))

    if fracpart or spec['alt']:
        fracpart = spec['decimal_point'] + fracpart

    if exp != 0 or spec['type'] in 'eE':
        echar = {'E': 'E', 'e': 'e', 'G': 'E', 'g': 'e'}[spec['type']]
        fracpart += "{0}{1:+}".format(echar, exp)
    if spec['type'] == '%':
        fracpart += '%'

    if spec['zeropad']:
        min_width = spec['minimumwidth'] - len(fracpart) - len(sign)
    else:
        min_width = 0
    intpart = _insert_thousands_sep(intpart, spec, min_width)

    return _format_align(sign, intpart+fracpart, spec)