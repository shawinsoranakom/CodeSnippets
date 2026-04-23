def eval(cls, base, exp):
        if isinstance(base, sympy.Integer) and isinstance(exp, sympy.Integer):
            r = safe_pow(base, exp)
            if r in (-int_oo, int_oo):
                return r
            return sympy.Integer(r)
        if isinstance(exp, sympy.Integer):
            # Rely on regular sympy Pow for this (note that iterated
            # multiplication turns into a Pow anyway, you can't escape!!)
            return sympy.Pow(base, exp)
        if exp in (int_oo, sympy.oo):
            if base.is_nonnegative:
                return int_oo
            elif base.is_negative:
                return sympy.zoo