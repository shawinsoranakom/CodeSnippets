def _check_args(x, div, mod, is_first):
            if not isinstance(div, sympy.Integer) or not isinstance(mod, sympy.Integer):
                return False
            if div != 1:
                return False
            if mod <= 0:
                return False

            if is_first:
                # first ModularIndexing should contains a nested ModularIndex
                if not isinstance(x, ModularIndexing):
                    return False
            else:
                # second ModularIndexing should contains a non-negative
                # symbol
                if not isinstance(x, sympy.Symbol) or not self.statically_known_geq(
                    x, 0
                ):
                    return False
            return True