def _paired(self, expressions, output_field):
        # wrap pairs of expressions in successive concat functions
        # exp = [a, b, c, d]
        # -> ConcatPair(a, ConcatPair(b, ConcatPair(c, d))))
        if len(expressions) == 2:
            return ConcatPair(*expressions, output_field=output_field)
        return ConcatPair(
            expressions[0],
            self._paired(expressions[1:], output_field=output_field),
            output_field=output_field,
        )