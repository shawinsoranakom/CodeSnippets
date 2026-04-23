def expand_floor_div(
        self, index: sympy.Expr
    ) -> bool | tuple[sympy.Expr, sympy.Expr]:
        """
        Expand the FloorDiv to the entire expression so that the expression may
        be simplified.

        E.g., for a 2D contiguous tensor with shape [a, 2 * b], and index variables
        x1, x2, index expression 'x1 * 2b + x2' can be easily combined.
        But index expression 'x1 * b + x2 // 2' can not.
        By expanding the FloorDiv to the entire expression, we get
        '(x1 * 2b + x2) // 2'. This transformation allows us to merge loops
        for the numerator!

        Return false if this optimization can be applied;
        Return the new expression and the denominator otherwise.
        The original expression will be equivalent to 'new_expression // denominator'
        """
        if not isinstance(index, sympy.Add):
            return False
        terms = index.args

        if len(terms) < 2:
            return False
        floor_div_index = -1
        varlist = []
        factorlist = []
        for idx, term in enumerate(terms):
            if isinstance(term, sympy.Mul):
                # For dynamic shape, term like '2*s1*x1' has 3 child nodes.
                # - A integer for 2
                # - A symbol for s1
                # - A symbol for x1
                # Skip for now.
                if len(term.args) != 2:
                    return False
                factor, var = term.args
                varlist.append(var)
                factorlist.append(factor)
                if not isinstance(factor, sympy.Integer) or not isinstance(
                    var, sympy.Symbol
                ):
                    return False
                # It's easier to reason about the correceness of the transformation
                # for non-negative integers.
                if not self.statically_known_geq(var, 0):
                    return False
            elif isinstance(term, FloorDiv):
                var, factor = term.args
                if not isinstance(factor, sympy.Integer) or not isinstance(
                    var, sympy.Symbol
                ):
                    return False
                if not self.statically_known_geq(var, 0):
                    return False
                if floor_div_index >= 0:
                    # can not handle multi FloorDiv yet
                    return False

                floor_div_index = idx
                varlist.append(var)
                # this factor is denominator
                factorlist.append(factor)
            else:
                return False

        if floor_div_index < 0:
            return False

        # Construct the new expression and remember the denominator
        denominator = factorlist[floor_div_index]
        new_index = sympy.S.Zero

        for var, factor, idx in zip(varlist, factorlist, itertools.count()):
            if idx == floor_div_index:
                new_index += var
            else:
                new_index += (factor * denominator) * var

        return new_index, denominator