def _find_localzeros(cls, values, **options):
        """
        Sequentially allocate values to localzeros.

        When a value is identified as being more extreme than another member it
        replaces that member; if this is never true, then the value is simply
        appended to the localzeros.

        Unlike the sympy implementation, we only look for zero and one, we don't
        do generic is connected test pairwise which is slow
        """

        # First, collapse all numeric arguments
        other_values = set()
        num_value = None
        for arg in values:
            if arg.is_Number:
                if num_value is None:
                    num_value = arg
                else:
                    if cls is Max:
                        num_value = max(num_value, arg)
                    elif cls is Min:
                        num_value = min(num_value, arg)
                    else:
                        raise AssertionError(f"impossible {cls}")
            else:
                other_values.add(arg)

        # Special cases when there is only one symbolic value
        if num_value is None:
            return other_values

        if len(other_values) == 0:
            return {num_value}

        if len(other_values) == 1:
            other_value = next(iter(other_values))
            if num_value in (0.0, 0) and other_value.is_nonnegative:
                return other_values if cls is Max else {num_value}
            if num_value == 1 and other_value.is_positive:
                return other_values if cls is Max else {num_value}

        other_values.add(num_value)
        return other_values