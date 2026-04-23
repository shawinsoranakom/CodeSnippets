def normalize(self, context=None):
        """Normalize- strip trailing 0s, change anything equal to 0 to 0e0"""

        if context is None:
            context = getcontext()

        if self._is_special:
            ans = self._check_nans(context=context)
            if ans:
                return ans

        dup = self._fix(context)
        if dup._isinfinity():
            return dup

        if not dup:
            return _dec_from_triple(dup._sign, '0', 0)
        exp_max = [context.Emax, context.Etop()][context.clamp]
        end = len(dup._int)
        exp = dup._exp
        while dup._int[end-1] == '0' and exp < exp_max:
            exp += 1
            end -= 1
        return _dec_from_triple(dup._sign, dup._int[:end], exp)