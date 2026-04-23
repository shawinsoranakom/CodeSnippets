def __hash__(self):
        """x.__hash__() <==> hash(x)"""

        # In order to make sure that the hash of a Decimal instance
        # agrees with the hash of a numerically equal integer, float
        # or Fraction, we follow the rules for numeric hashes outlined
        # in the documentation.  (See library docs, 'Built-in Types').
        if self._is_special:
            if self.is_snan():
                raise TypeError('Cannot hash a signaling NaN value.')
            elif self.is_nan():
                return object.__hash__(self)
            else:
                if self._sign:
                    return -_PyHASH_INF
                else:
                    return _PyHASH_INF

        if self._exp >= 0:
            exp_hash = pow(10, self._exp, _PyHASH_MODULUS)
        else:
            exp_hash = pow(_PyHASH_10INV, -self._exp, _PyHASH_MODULUS)
        hash_ = int(self._int) * exp_hash % _PyHASH_MODULUS
        ans = hash_ if self >= 0 else -hash_
        return -2 if ans == -1 else ans