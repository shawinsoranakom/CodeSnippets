def _format_float_style(self, match):
        """Helper method for __format__; handles float presentation types."""
        fill = match["fill"] or " "
        align = match["align"] or ">"
        pos_sign = "" if match["sign"] == "-" else match["sign"]
        no_neg_zero = bool(match["no_neg_zero"])
        alternate_form = bool(match["alt"])
        zeropad = bool(match["zeropad"])
        minimumwidth = int(match["minimumwidth"] or "0")
        thousands_sep = match["thousands_sep"]
        precision = int(match["precision"] or "6")
        frac_sep = match["frac_separators"] or ""
        presentation_type = match["presentation_type"]
        trim_zeros = presentation_type in "gG" and not alternate_form
        trim_point = not alternate_form
        exponent_indicator = "E" if presentation_type in "EFG" else "e"

        if align == '=' and fill == '0':
            zeropad = True

        # Round to get the digits we need, figure out where to place the point,
        # and decide whether to use scientific notation. 'point_pos' is the
        # relative to the _end_ of the digit string: that is, it's the number
        # of digits that should follow the point.
        if presentation_type in "fF%":
            exponent = -precision
            if presentation_type == "%":
                exponent -= 2
            negative, significand = _round_to_exponent(
                self._numerator, self._denominator, exponent, no_neg_zero)
            scientific = False
            point_pos = precision
        else:  # presentation_type in "eEgG"
            figures = (
                max(precision, 1)
                if presentation_type in "gG"
                else precision + 1
            )
            negative, significand, exponent = _round_to_figures(
                self._numerator, self._denominator, figures)
            scientific = (
                presentation_type in "eE"
                or exponent > 0
                or exponent + figures <= -4
            )
            point_pos = figures - 1 if scientific else -exponent

        # Get the suffix - the part following the digits, if any.
        if presentation_type == "%":
            suffix = "%"
        elif scientific:
            suffix = f"{exponent_indicator}{exponent + point_pos:+03d}"
        else:
            suffix = ""

        # String of output digits, padded sufficiently with zeros on the left
        # so that we'll have at least one digit before the decimal point.
        digits = f"{significand:0{point_pos + 1}d}"

        # Before padding, the output has the form f"{sign}{leading}{trailing}",
        # where `leading` includes thousands separators if necessary and
        # `trailing` includes the decimal separator where appropriate.
        sign = "-" if negative else pos_sign
        leading = digits[: len(digits) - point_pos]
        frac_part = digits[len(digits) - point_pos :]
        if trim_zeros:
            frac_part = frac_part.rstrip("0")
        separator = "" if trim_point and not frac_part else "."
        if frac_sep:
            frac_part = frac_sep.join(frac_part[pos:pos + 3]
                                      for pos in range(0, len(frac_part), 3))
        trailing = separator + frac_part + suffix

        # Do zero padding if required.
        if zeropad:
            min_leading = minimumwidth - len(sign) - len(trailing)
            # When adding thousands separators, they'll be added to the
            # zero-padded portion too, so we need to compensate.
            leading = leading.zfill(
                3 * min_leading // 4 + 1 if thousands_sep else min_leading
            )

        # Insert thousands separators if required.
        if thousands_sep:
            first_pos = 1 + (len(leading) - 1) % 3
            leading = leading[:first_pos] + "".join(
                thousands_sep + leading[pos : pos + 3]
                for pos in range(first_pos, len(leading), 3)
            )

        # We now have a sign and a body. Pad with fill character if necessary
        # and return.
        body = leading + trailing
        padding = fill * (minimumwidth - len(sign) - len(body))
        if align == ">":
            return padding + sign + body
        elif align == "<":
            return sign + body + padding
        elif align == "^":
            half = len(padding) // 2
            return padding[:half] + sign + body + padding[half:]
        else:  # align == "="
            return sign + padding + body