def call_binop(self, context, operator, left, right):
        # Intercept the ** (power) operator
        if operator == "**":
            if isinstance(right, (int, float)) and abs(right) > MAX_EXPONENT:
                raise OverflowError(f"Exponent too large (max {MAX_EXPONENT})")
            if isinstance(left, (int, float)) and abs(left) > MAX_EXPONENT:
                raise OverflowError(
                    f"Base too large for exponentiation (max {MAX_EXPONENT})"
                )
        # Intercept sequence repetition via * (strings, lists, tuples)
        if operator == "*":
            if isinstance(left, (str, list, tuple)) and isinstance(right, int):
                if len(left) * right > MAX_SEQUENCE_REPEAT:
                    raise OverflowError(
                        f"Sequence repeat too large (max {MAX_SEQUENCE_REPEAT} items)"
                    )
            if isinstance(right, (str, list, tuple)) and isinstance(left, int):
                if len(right) * left > MAX_SEQUENCE_REPEAT:
                    raise OverflowError(
                        f"Sequence repeat too large (max {MAX_SEQUENCE_REPEAT} items)"
                    )
        return super().call_binop(context, operator, left, right)