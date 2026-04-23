def __init__(self, lower: AllIn, upper: AllIn) -> None:
        lower = simple_sympify(lower)
        upper = simple_sympify(upper)
        # TODO: when the bounds have free variables, this may be
        # nontrivial to actually verify
        try:
            if not sympy_generic_le(lower, upper):
                raise ValueRangeError(f"Invalid ranges [{lower}:{upper}]")
        except TypeError as e:
            raise TypeError(f"Could not compare {lower} <= {upper}") from e

        is_bool_lower = isinstance(lower, SympyBoolean)
        is_bool_upper = isinstance(upper, SympyBoolean)
        if is_bool_lower != is_bool_upper:
            raise AssertionError((lower, upper))

        # Warning: is_int/is_float is best effort.  We do pretty well in
        # Dynamo, but in Inductor these attributes are often wrong because we
        # are not very rigorous in dtype analysis.  This is also why we need
        # the flexible analysis for is_int: sometimes a sympy.oo pops in for
        # an integer bound. I would /like/ for us not to do this, but it's
        # too hard to push the invariant through right now.
        if isinstance(lower, sympy.Integer) and upper == sympy.oo:
            upper = int_oo
        if isinstance(upper, sympy.Integer) and lower == -sympy.oo:
            lower = -int_oo
        # NB: [-int_oo, -int_oo] and [int_oo, int_oo] are allowed
        integer_types = (sympy.Integer, NegativeIntInfinity, IntInfinity)
        is_int_lower = isinstance(lower, integer_types)
        is_int_upper = isinstance(upper, integer_types)

        # Because this is a frozen class
        object.__setattr__(self, "lower", lower)
        object.__setattr__(self, "upper", upper)
        # Unlike bool/int in Python, we don't report bools are ints
        #
        # NB: is_bool_lower == is_bool_upper, so we only need to check one
        object.__setattr__(self, "is_bool", is_bool_lower)
        object.__setattr__(
            self,
            "is_int",
            not self.is_bool and is_int_lower and is_int_upper,
        )
        """
        # This assert is just impossible right now, too many sympy bugs
        if self.is_int:
            # NB: sympy will sometimes randomly lose the float-ness of zero,
            # so we also need to account for that in the assertion here.
            # See also https://github.com/sympy/sympy/issues/26620
            assert isinstance(lower, sympy.Integer) or lower in [-sympy.oo, 0], (
                lower,
                upper,
            )
            assert isinstance(upper, sympy.Integer) or upper in [sympy.oo, 0], (lower, upper)
        """
        # NB: [-oo, oo] always advertises as float!
        object.__setattr__(self, "is_float", not self.is_bool and not self.is_int)
        if not self.is_bool and not self.is_int and not self.is_float:
            raise AssertionError((lower, upper))