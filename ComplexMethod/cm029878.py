def _format_general(self, match):
        """Helper method for __format__.

        Handles fill, alignment, signs, and thousands separators in the
        case of no presentation type.
        """
        # Validate and parse the format specifier.
        fill = match["fill"] or " "
        align = match["align"] or ">"
        pos_sign = "" if match["sign"] == "-" else match["sign"]
        alternate_form = bool(match["alt"])
        minimumwidth = int(match["minimumwidth"] or "0")
        thousands_sep = match["thousands_sep"] or ''

        # Determine the body and sign representation.
        n, d = self._numerator, self._denominator
        if d > 1 or alternate_form:
            body = f"{abs(n):{thousands_sep}}/{d:{thousands_sep}}"
        else:
            body = f"{abs(n):{thousands_sep}}"
        sign = '-' if n < 0 else pos_sign

        # Pad with fill character if necessary and return.
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