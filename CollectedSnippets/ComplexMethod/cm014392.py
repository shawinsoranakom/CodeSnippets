def _identity_atom_compare(self, other, op):
        """
        Fast path for comparing wrapped numeric atomics against other numeric atomics.
        Keep compound expressions on SymPy's default symbolic path.
        """
        arg = self.args[0]
        if isinstance(other, int):
            other = sympy.Integer(other)
        if not isinstance(other, sympy.Expr):
            return None
        if not (arg.is_Atom and arg.is_number and arg.is_comparable):
            return None
        if not (other.is_Atom and other.is_number and other.is_comparable):
            return None
        return sympy.S.true if op(arg, other) else sympy.S.false